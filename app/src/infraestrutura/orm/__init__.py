from infraestrutura.orm.orm_agendamento import agendamentos_tabela
from infraestrutura.orm.orm_auditoria import auditorias_tabela
from infraestrutura.orm.orm_conversa import conversas_tabela, mensagens_tabela
from infraestrutura.orm.orm_empresa import empresas_tabela
from infraestrutura.orm.orm_lead import leads_tabela
from infraestrutura.orm.orm_turno_ia import turnos_ia_tabela

__all__ = [
    "agendamentos_tabela",
    "auditorias_tabela",
    "conversas_tabela",
    "empresas_tabela",
    "leads_tabela",
    "mensagens_tabela",
    "turnos_ia_tabela",
]
