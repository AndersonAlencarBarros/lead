from dataclasses import dataclass
from datetime import datetime

from dominio.objetos_de_valor.conversa import Mensagem, Telefone


@dataclass
class Conversa:
    id: int
    empresa_id: str
    lead_id: str
    telefone: Telefone
    mensagens: list[Mensagem]
    criado_em: datetime
    teve_intervencao_humana: bool = False


    def receber_mensagem(self, mensagem: Mensagem) -> None:
        # Validar duplicidade e registrar mensagem
        ...

    def ativar_intervencao_humana(self) -> None:
        self.teve_intervencao_humana = True

    def desativar_intervencao_humana(self) -> None:
        self.teve_intervencao_humana = False

    def ia_pode_responder(self) -> bool:
        return not self.teve_intervencao_humana
