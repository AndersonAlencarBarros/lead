from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento, Telefone


class Agendamento(Agregado):
    id: UUID
    empresa_id: UUID
    lead_id: UUID
    telefone: Telefone
    horario_agendado: datetime
    status: StatusDoAgendamento
    criado_em: datetime

    def confirmar_agendamento(self):
        self.status = StatusDoAgendamento("confirmado")

    def cancelar_agendamento(self):
        self.status = StatusDoAgendamento("cancelado")
