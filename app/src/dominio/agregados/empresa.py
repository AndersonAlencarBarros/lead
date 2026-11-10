from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.empresa import (
    Cidade,
    ConfiguracaoIA,
    Estagio,
    RegrasGerais,
    StatusEmpresa,
    Telefone,
)


class Empresa(Agregado):
    id: UUID
    tenant_id: str
    nome: str
    status: StatusEmpresa
    configuracao_ia: ConfiguracaoIA
    regras_gerais: list[RegrasGerais]
    cidades_atendidas: list[Cidade]
    telefone_notificacao: Telefone
    estagios: list[Estagio]
    criado_em: datetime
    janela_de_resposta: float = (
        10  # tempo em segundos que será considerado para resposta
    )

    def ativar(self):
        self.status = StatusEmpresa.ATIVA

    def desativar(self):
        self.status = StatusEmpresa.INATIVA

    def cidade_atendida(self, cidade: str) -> bool:
        return any(cidade.casefold() == c.casefold() for c in self.cidades_atendidas)

    def estagio_permitido(self, estagio: str) -> bool:
        return estagio in self.estagios
