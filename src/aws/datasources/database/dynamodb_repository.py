from aws.datasources.database.dynamodb_interface import DynamoDBInterface
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO
import boto3
import logging

logger = logging.getLogger(__name__)


class DynamoDBRepository(DynamoDBInterface):

    def __init__(self, table_name: str, region: str):
        self.table_name = table_name
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)


    def get_metadata_by_video_id(self, video_id: str) -> VdscMetadataDTO:
        try:
            print(f"Buscando metadados para vídeo: {video_id}")
            response = self.dynamodb_client.get_item(TableName=self.table_name,Key={'videoId': {'S': video_id}})
            if 'Item' not in response:
                logger.warning(f"Vídeo não encontrado: {video_id}")
                raise ValueError(f"Vídeo com ID {video_id} não encontrado")

            item = response['Item']
            vdsc_metadata_dto = VdscMetadataDTO.from_dynamodb_item(item)

            logger.info(f"Metadados recuperados para vídeo: {video_id}")
            return vdsc_metadata_dto

        except Exception as ex:
            logger.error(f"Erro ao buscar metadados do vídeo {video_id}: {str(ex)}", exc_info=True)
            raise

    def update_metadata_by_video_id(self, update_data: VdscMetadataDTO) -> VdscMetadataDTO:
        """Atualiza metadados do vídeo no DynamoDB recebendo um DTO"""
        video_id = None
        try:
            # Converter DTO para formato DynamoDB
            dynamodb_data = update_data.to_dynamodb_item()

            video_id = self._extract_video_id(dynamodb_data)
            logger.info(f"Atualizando metadados para vídeo: {video_id}")

            fields_to_update = self._filter_fields_to_update(dynamodb_data)
            update_expression, expression_names, expression_values = self._build_update_expression(fields_to_update)
            updated_item = self._execute_update(video_id, update_expression, expression_names, expression_values)
            vdsc_metadata_dto = self._convert_to_dto(updated_item)

            logger.info(f"Metadados atualizados com sucesso para o vídeo: {video_id}")
            return vdsc_metadata_dto

        except Exception as ex:
            logger.error(f"Erro ao atualizar metadados do vídeo: {str(ex)}", exc_info=True)
            raise

    def _extract_video_id(self, update_data: dict) -> str:
        """Extrai o videoId do formato DynamoDB"""
        if 'videoId' not in update_data:
            raise ValueError("O campo 'videoId' é obrigatório em update_data")

        video_id = update_data['videoId'].get('S')
        if not video_id:
            raise ValueError("O campo 'videoId' deve ter o formato {'S': 'valor'}")

        return video_id

    def _filter_fields_to_update(self, update_data: dict) -> dict:
        """Remove o videoId dos campos a serem atualizados"""
        fields_to_update = {k: v for k, v in update_data.items() if k != 'videoId'}

        if not fields_to_update:
            raise ValueError("Nenhum campo para atualizar foi fornecido")

        return fields_to_update

    def _build_update_expression(self, fields_to_update: dict) -> tuple:
        """Constrói a expressão de atualização do DynamoDB"""
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for idx, (field, value) in enumerate(fields_to_update.items()):
            placeholder_name = f"#field{idx}"
            placeholder_value = f":value{idx}"

            update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
            expression_attribute_names[placeholder_name] = field
            expression_attribute_values[placeholder_value] = value

        update_expression = "SET " + ", ".join(update_expression_parts)

        return update_expression, expression_attribute_names, expression_attribute_values

    def _execute_update(self, video_id: str, update_expression: str,
                        expression_attribute_names: dict,
                        expression_attribute_values: dict) -> dict:
        """Executa a operação de update no DynamoDB"""
        response = self.dynamodb_client.update_item(
            TableName=self.table_name,
            Key={'videoId': {'S': video_id}},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )

        if 'Attributes' not in response:
            raise ValueError(f"Vídeo com ID {video_id} não encontrado")

        return response['Attributes']

    def _convert_to_dto(self, item: dict) -> VdscMetadataDTO:
        """Converte item do DynamoDB para DTO"""
        return VdscMetadataDTO.from_dynamodb_item(item)
