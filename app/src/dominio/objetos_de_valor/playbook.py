from dataclasses import dataclass

from dominio.objetos_de_valor.ferramenta import NomeFerramenta


@dataclass(frozen=True)
class Playbook:
    nome: str
    objetivo: str
    perguntas: tuple[str, ...]
    criterios_de_qualificacao: tuple[str, ...]
    regras: tuple[str, ...]
    ferramentas: tuple[NomeFerramenta, ...]
    versao: int = 1
