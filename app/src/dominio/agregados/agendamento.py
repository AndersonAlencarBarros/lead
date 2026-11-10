from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento, Telefone


class Agendamento(Agregado):
    id: UUID | None
    empresa_id: UUID
    lead_id: UUID
    telefone: Telefone
    horario_agendado: datetime
    status: StatusDoAgendamento
    criado_em: datetime

    def __init__(
        self,
        empresa_id: UUID,
        lead_id: UUID,
        telefone: str,
        horario_agendado: datetime,
        status: StatusDoAgendamento = StatusDoAgendamento.CONFIRMADO,
        id: UUID | None = None,
        criado_em: datetime | None = None,
    ):
        self.id = id
        self.empresa_id = empresa_id
        self.lead_id = lead_id
        self.telefone = Telefone(telefone)
        self.horario_agendado = horario_agendado
        self.status = StatusDoAgendamento(status)
        self.criado_em = criado_em or datetime.now()

    def confirmar_agendamento(self):
        self.status = StatusDoAgendamento.CONFIRMADO

    def cancelar_agendamento(self):
        self.status = StatusDoAgendamento.CANCELADO
