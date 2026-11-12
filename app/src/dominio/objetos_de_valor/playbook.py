from dataclasses import dataclass
from enum import StrEnum

from dominio.objetos_de_valor.ferramenta import NomeFerramenta


class TipoCampo(StrEnum):
    TEXTO = "texto"
    NUMERO = "numero"
    DATA = "data"
    OPCAO = "opcao"


@dataclass(frozen=True)
class CampoDaFicha:
    nome: str
    descricao: str
    tipo: TipoCampo
    opcoes: tuple[str, ...] = ()
    obrigatorio: bool = False


@dataclass(frozen=True)
class Playbook:
    nome: str
    objetivo: str
    perguntas: tuple[str, ...]
    campos: tuple[CampoDaFicha, ...]
    criterios_de_qualificacao: tuple[str, ...]
    regras: tuple[str, ...]
    ferramentas: tuple[NomeFerramenta, ...]
    versao: int = 1

    def campo(self, nome: str) -> CampoDaFicha | None:
        return next((campo for campo in self.campos if campo.nome == nome), None)
