from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.conversa import Mensagem, Telefone


class Conversa(Agregado):
    id: UUID | None
    tenant_id: str
    lead_id: UUID | None
    telefone: Telefone
    criado_em: datetime
    mensagens: list[Mensagem]
    teve_intervencao_humana: bool = False

    def __init__(
        self,
        tenant_id: str,
        telefone: str,
        lead_id: UUID | None = None,
        id: UUID | None = None,
        mensagens: list[Mensagem] | None = None,
        criado_em: datetime | None = None,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.lead_id = lead_id
        self.telefone = Telefone(telefone)
        self.criado_em = criado_em or datetime.now()
        self.mensagens = mensagens or []

    def receber_mensagem(self, mensagem: Mensagem) -> None:
        self.mensagens.append(mensagem)

    def ativar_intervencao_humana(self) -> None:
        self.teve_intervencao_humana = True

    def desativar_intervencao_humana(self) -> None:
        self.teve_intervencao_humana = False

    def ia_pode_responder(self) -> bool:
        return not self.teve_intervencao_humana
