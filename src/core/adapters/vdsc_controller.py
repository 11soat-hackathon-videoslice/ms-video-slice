from ..interfaces.vdsc_controller_interface import VdscControllerInterface
from ..interfaces.vdsc_dataproxy_interface import VdscDataProxyInterface
from ..interfaces.vdsc_exception_handler_interface import VdscExceptionHandlerInterface
from ..dtos.vdsc_metadata_dto import VdscMetadataDTO
from .vdsc_gateway import VdscGateway
from ..applications.video_process_use_case import VdscProcessUseCase

class VdscController(VdscControllerInterface):

    def __init__(self, dataproxy: VdscDataProxyInterface, handler: VdscExceptionHandlerInterface):
        self.data_proxy = dataproxy
        self.handler = handler

    def video_slice_processing(self, event: VdscMetadataDTO, config: dict) -> dict:
        gateway = VdscGateway(self.data_proxy)
        use_case = VdscProcessUseCase()
        use_case.execute(gateway, event, config, self.handler)







