from dataclasses import dataclass
from datetime import datetime

from dominio.objetos_de_valor.lead import Cidade, EstagioDoLead, Nome, Telefone


@dataclass
class Lead:
    id: str
    empresa_id: str
    nome: Nome | None
    telefone: Telefone | None
    cidade: Cidade | None
    estagio: EstagioDoLead | None
    criado_em: datetime

    def mover_estagio(self, tag: str | EstagioDoLead):
        self.estagio = EstagioDoLead(tag)