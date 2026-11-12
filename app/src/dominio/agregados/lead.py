from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.lead import Cidade, Nome, Telefone


class Lead(Agregado):
    id: UUID | None
    empresa_id: UUID
    nome: Nome | None
    telefone: Telefone | None
    cidade: Cidade | None
    estagio: str | None
    criado_em: datetime

    def __init__(
        self,
        empresa_id: UUID,
        nome: str | None = None,
        telefone: str | None = None,
        cidade: str | None = None,
        estagio: str | None = None,
        id: UUID | None = None,
        criado_em: datetime | None = None,
    ):
        self.id = id
        self.empresa_id = empresa_id
        self.nome = Nome(nome) if nome is not None else None
        self.telefone = Telefone(telefone) if telefone is not None else None
        self.cidade = Cidade(cidade) if cidade is not None else None
        self.estagio = estagio
        self.criado_em = criado_em or datetime.now()

    def mover_estagio(self, estagio: str) -> None:
        self.estagio = estagio
