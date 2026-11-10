from dataclasses import dataclass
from datetime import datetime

from dominio.objetos_de_valor.agendamento import StatusDoAgendamento


@dataclass
class Agendamento:
    id: str
    empresa_id: str
    lead_id: str
    horario_agendado: datetime
    status: StatusDoAgendamento
    criado_em: datetime

    def confirmar_agendamento(self):
        self.status = StatusDoAgendamento("confirmado")

    def cancelar_agendamento(self):
        self.status = StatusDoAgendamento("cancelado")