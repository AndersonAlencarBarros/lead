from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.lead import Cidade, EstagioDoLead, Nome, Telefone


class Lead(Agregado):
    id: UUID
    empresa_id: UUID
    nome: Nome | None
    telefone: Telefone | None
    cidade: Cidade | None
    estagio: EstagioDoLead | None
    criado_em: datetime

    def mover_estagio(self, tag: str | EstagioDoLead):
        self.estagio = EstagioDoLead(tag)
