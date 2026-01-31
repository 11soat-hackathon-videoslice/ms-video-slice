import io
import logging
import tempfile
import zipfile

import cv2

from pathlib import Path
from ..interfaces.vdsc_gateway_interface import VdscGatewayInferface
from ..dtos.vdsc_metadata_dto import VdscMetadataDTO
from ..domain.vdsc_metadata import VdscMetadata, LogEntry
from ..enums.vdsc_status_enum import VdscStatusEnum
from ..exceptions.vdsc_exceptions import VdscException
from ..interfaces.vdsc_exception_handler_interface import VdscExceptionHandlerInterface
from ..utils import get_event_schedule_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VdscProcessUseCase:

    def execute(self, gateway: VdscGatewayInferface, event: VdscMetadataDTO, config: dict, handler: VdscExceptionHandlerInterface):
        """Executa o processamento de vídeo com tratamento de exceções via handler injetado"""
        logger.info(f"Iniciando o caso de uso de processamento de vídeo para o vídeo ID: {event.video_id}")

        #Construindo entidade de domínio a partir do DTO
        vdsc_metadata = VdscMetadata(dto=event)
        video_id = vdsc_metadata.video_id
        retries = vdsc_metadata.retries
        max_retries = vdsc_metadata.max_retry
        extension_file = vdsc_metadata.extension_file

        try:
            # Atualizando status de metadados para Processing ou Retrying
            if vdsc_metadata.status.upper() == VdscStatusEnum.UPLOADED.value.upper():
                vdsc_metadata = self._metadata_update_status(vdsc_metadata, VdscStatusEnum.PROCESSING, LogEntry(f"Iniciando processamento do vídeo: {video_id}"))
            elif vdsc_metadata.status.upper() == VdscStatusEnum.RETRYING.value.upper():
                retries += 1
                vdsc_metadata.retries = retries
                log_message = f"Reiniciando processamento do vídeo: {video_id}. Tentativa {retries} de {max_retries}."
                vdsc_metadata = self._metadata_update_status(vdsc_metadata, VdscStatusEnum.RETRYING, LogEntry(log_message))
            gateway.update_metadata(vdsc_metadata)

            # Movendo arquivo para área de processamento
            file_uploaded_path = self._get_path_file(path_type = 'uploads', video_id=video_id, extension_file=extension_file, config=config)
            file_processing_path = self._get_path_file(path_type = 'processing', video_id=video_id, extension_file=extension_file, config=config)
            gateway.move_file(file_uploaded_path, file_processing_path)

            #Criando diretório para imagens processadas
            video_output_directory = self._get_path_directory(path_type = 'processing', video_id=video_id,config=config)
            gateway.create_directory(video_output_directory)

            #Abrindo arquivo de video para processamento
            video_data = gateway.open_file(file_processing_path)

            #Processamento de caputura de frames
            logger.info(f"Iniciando captura de imagens para o vídeo ID: {event.video_id}")
            self._process_video_frames(video_id, vdsc_metadata, video_data, video_output_directory, gateway, config)
            logger.info(f"Finalizada captura de imagens para o vídeo ID: {event.video_id})")

            #Compactando arquivos para zip
            zip_output_path = self._get_path_file(path_type = 'finished', video_id=video_id, extension_file='zip', config=config)
            self._compress_images_to_zip(video_output_directory, zip_output_path, gateway, config)

            #Deletando diretório de imagens processadas
            gateway.delete_files_by_directory(video_output_directory)

            #Deletando video processado
            gateway.delete_file(file_processing_path)

            #Atualizando metadados para finalizado
            vdsc_metadata = self._metadata_update_status(vdsc_metadata, VdscStatusEnum.FINISHED, LogEntry("Processamento finalizado com sucesso."))
            gateway.update_metadata(vdsc_metadata)

            logger.info(f"Processamento concluído com sucesso para o vídeo ID: {event.video_id}")

        except Exception as ex:
            logger.error(f"Erro ao processar o vídeo ID {event.video_id}: {str(ex)}", exc_info=ex)

            if retries == max_retries:
                vdsc_metadata_error, message = self._set_exception_status(gateway, ex, vdsc_metadata, VdscStatusEnum.FAILED, config)
            else:
                vdsc_metadata_error, message = self._set_exception_status(gateway, ex, vdsc_metadata, VdscStatusEnum.RETRYING, config)

            if vdsc_metadata_error:
                vdsc_metadata = vdsc_metadata_error
                gateway.update_metadata(vdsc_metadata_error)
                gateway.send_notification(vdsc_metadata_error, ['email'], message)
            raise VdscException(message, "ERROR", vdsc_metadata_error.to_dict())

    def _compress_images_to_zip(self, output_directory: str, zip_directory: str, gateway: VdscGatewayInferface,
                                config: dict) -> None:
        #Cria lista com nome e dados dos arquivos
        file_info_list = self._get_file_info_list(output_directory, gateway)

        #Cria buffer zip informando nível de compressão
        buffer_zip = self._create_zip_buffer(file_info_list, config.vdsc['zip_compression_level'])

        #Salva arquivo zip no S3
        gateway.save_file(zip_directory, buffer_zip.read())

    def _create_temporary_file(self, video_data, file_extension) -> str:
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
            temp_file.write(video_data)
            temp_file_path = temp_file.name
        return temp_file_path

    def _create_interval_list(self, vdsc_metadata, time_unit_multiplier ):

        start_time = int(vdsc_metadata.start_time * time_unit_multiplier)
        logger.info(f"start_time: {start_time}")
        end_time = int(vdsc_metadata.end_time * time_unit_multiplier)
        logger.info(f"end_time: {end_time}")
        interval = int(vdsc_metadata.time_interval[0]) * int(time_unit_multiplier)
        logger.info(f"interval: {interval}")

        if len(vdsc_metadata.time_interval) == 1:
            time_interval_list = self._get_recurrent_time_intervals(start_time, end_time, interval)
        else:
            time_interval_list = self._get_specific_time_intervals(vdsc_metadata.time_interval, int(time_unit_multiplier))
        return time_interval_list

    def _create_zip_buffer(self, file_info_list: list[tuple[str, bytes]], compression_level: int) -> io.BytesIO:
        """Cria um buffer zip com os arquivos fornecidos"""
        buffer_zip = io.BytesIO()
        with zipfile.ZipFile(buffer_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zip_file:
            for file_name, file_data in file_info_list:
                zip_file.writestr(file_name, file_data)
        buffer_zip.seek(0)
        return buffer_zip

    def _encode_frame_to_png(self, frame, png_compression: int):
        return cv2.imencode('.png', frame, [cv2.IMWRITE_PNG_COMPRESSION, png_compression])

    def _frame_resize(self, frame, target_width: int, target_height: int):
        """Redimensiona o frame para as dimensões especificadas"""
        return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

    def _get_file_info_list(self, output_directory, gateway):
        """Retorna uma lista de tuplas (nome_arquivo, dados_arquivo) do diretório informado"""
        file_list = gateway.get_list_paths_by_directory(output_directory)
        file_info_list = []
        for file_path in file_list:
            file_name = Path(file_path).name
            file_data = gateway.open_file(file_path)
            file_info_list.append((file_name, file_data))
        return file_info_list

    def _get_frame_size(self, frame, target_height: int):
        original_h, original_w = frame.shape[:2]
        if original_h <= target_height:
            return frame
        ratio = target_height / float(original_h)
        target_width = int(original_w * ratio)
        return target_height, target_width

    def _get_multiplier_time_unit(self, time_unit: str) -> int:
        return 1000 if time_unit == 's' else 1

    def _get_path_file(self, path_type, video_id, extension_file, config)-> str:
        """Retorna o caminho completo do arquivo"""
        dir_key = "dir_" + path_type
        return f"{config.s3_bucket[dir_key]}{video_id}.{extension_file}"

    def _get_path_directory(self, path_type, video_id, config) -> str:
        """Retorna o caminho completo do diretório"""
        dir_key = "dir_" + path_type
        return f"{config.s3_bucket[dir_key]}{video_id}/"

    def _get_recurrent_time_intervals(self, start_time: int, end_time: int, interval: int):
        logger.info("Gerando intervalos de tempo recorrentes")
        current_time = start_time
        time_interval_list = []
        while current_time <= end_time:
            time_interval_list.append(current_time)
            current_time += interval
            logger.info(f"time_interval_list: {time_interval_list}")
        return time_interval_list

    def _get_specific_time_intervals(self, time_intervals, multiplier: int) -> list[int]:
        """Converte intervalos de tempo específicos para milissegundos"""
        logger.info("Convertendo intervalos de tempo específicos para milissegundos")
        return [int(time) * int(multiplier) for time in time_intervals]

    def _get_frame_widths(self, frame, target_height: int):
        original_height, original_width = frame.shape[:2]
        ratio = target_height / float(original_height)
        target_width = int(original_width * ratio)
        return target_width, original_width

    def _metadata_update_status(self, vdsc_metadata: VdscMetadata, new_status: VdscStatusEnum, log: LogEntry) -> VdscMetadata:
        """Atualiza status e adiciona log aos metadados"""
        vdsc_metadata.status = new_status.value
        vdsc_metadata.logs.append(log)
        return vdsc_metadata

    def _process_video_frames(self, video_id, vdsc_metadata, video_data, video_output_directory, gateway, config):
        """Processa os frames do vídeo e salva as imagens"""
        time_unit_multiplier = self._get_multiplier_time_unit(vdsc_metadata.unit_time)
        logger.info(f"time_unit_multiplier: {time_unit_multiplier}")
        video_temp_path = self._create_temporary_file(video_data, vdsc_metadata.extension_file)
        logger.info(f"video_temp_path: {video_temp_path}")
        output_quality = vdsc_metadata.quality
        logger.info(f"output_quality: {output_quality}")
        png_compression = config.vdsc['png_compression_level']
        logger.info(f"png_compression: {png_compression}")


        try:
            vidcap = cv2.VideoCapture(video_temp_path)
            interval_list = self._create_interval_list(vdsc_metadata, time_unit_multiplier)
            target_frame_height = config.vdsc['quality'][output_quality]
            target_frame_width = None
            original_width = None

            for time_ms in interval_list:
                logger.info("Capturando frame no tempo(ms): {time_ms}")
                vidcap.set(cv2.CAP_PROP_POS_MSEC, time_ms)
                success, frame = vidcap.read()

                if not success:
                    logger.warning(f"Falha ao ler frame no tempo {time_ms}ms")
                    continue
                suffix_time_file = f"{int(time_ms/time_unit_multiplier)}_{vdsc_metadata.unit_time}"
                logger.info(f"suffix_time_file: {suffix_time_file}")
                file_output = f"{video_output_directory}{video_id}_{output_quality}_{suffix_time_file}.png"
                logger.info(f"file_output: {file_output}")

                if target_frame_width is None:
                    target_frame_width, original_width = self._get_frame_widths(frame, target_frame_height)
                    logger.info(f"target_frame_width: {target_frame_width}")
                    logger.info(f"original_width: {original_width}")

                if target_frame_width != original_width:
                    logger.info(f"Necesaria redimensionar frame para {target_frame_width}x{target_frame_height}")
                    frame = self._frame_resize(frame, target_frame_width, target_frame_height)

                success, png_data = self._encode_frame_to_png(frame, png_compression)
                if success:
                    gateway.save_file(file_output, png_data.tobytes())
                    logger.info(f"Frame salvo com sucesso em: {file_output}")
            vidcap.release()
        except Exception as e:
            logger.error(f"Erro ao processar frames do vídeo ID {video_id}: {str(e)}", exc_info=e)
            raise

    def _set_exception_status(self, gateway: VdscGatewayInferface, ex: Exception, vdsc_metadata: VdscMetadata, new_status: VdscStatusEnum, config: dict):
        retries = vdsc_metadata.retries
        max_retries = vdsc_metadata.max_retry

        match new_status:
            case VdscStatusEnum.FAILED:
                message = f"Processamento do video {vdsc_metadata.video_id} falhou após {max_retries} tentativas: {str(ex)}."
                vdsc_metadata = self._metadata_update_status(vdsc_metadata, new_status, LogEntry(f"Processamento falhou após {max_retries} tentativas."))
                return vdsc_metadata, message
            case VdscStatusEnum.RETRYING:
                vdsc_metadata.retries += 1
                message = f"Falha no processamento do video {vdsc_metadata.video_id}: {str(ex)}. Iniciando tentativa {retries+1} de {max_retries}."
                vdsc_metadata = self._metadata_update_status(vdsc_metadata, new_status, LogEntry(message))
                schedule_timestamp = get_event_schedule_timestamp(vdsc_metadata, retry_backoff_factor = config.vdsc['schedule_event_rules']['retry_backoff_factor'])
                gateway.send_schedule_retry_event(vdsc_metadata, schedule_timestamp, config.vdsc['schedule_event_rules'])
                return vdsc_metadata, message
        return None














