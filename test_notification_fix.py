"""Script de teste rápido para validar a correção do send_notification"""
from unittest.mock import Mock
from src.aws.dataproxy.vdsc_dataproxy import VdscDataProxy
from core.dtos.notification_dto import NotificationDto

# Criar mocks
mock_dynamodb = Mock()
mock_s3 = Mock()
mock_event_producer = Mock()

# Criar dataproxy
dataproxy = VdscDataProxy(
    dynamodb=mock_dynamodb,
    s3=mock_s3,
    event_producer=mock_event_producer
)

# Criar mock de notificação
mock_notification = Mock(spec=NotificationDto)

# Testar send_notification
try:
    dataproxy.send_notification(mock_notification)
    print("✓ send_notification funciona corretamente")
    print(f"✓ event_producer.send_notification foi chamado: {mock_event_producer.send_notification.called}")
    print(f"✓ Argumentos passados: {mock_event_producer.send_notification.call_args}")
except TypeError as e:
    print(f"✗ Erro: {e}")
    exit(1)

print("\n✓ Todos os testes passaram!")

