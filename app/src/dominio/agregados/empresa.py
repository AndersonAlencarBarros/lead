from datetime import datetime
from uuid import UUID

from dominio.agregados import Agregado
from dominio.objetos_de_valor.empresa import (
    Cidade,
    ConfiguracaoIA,
    DadosEmpresa,
    Estagio,
    RegrasGerais,
    StatusEmpresa,
    Telefone,
)
from dominio.objetos_de_valor.playbook import Playbook


def _playbook_padrao() -> Playbook:
    return Playbook(
        nome="padrao",
        objetivo="Atender o lead e coletar dados.",
        perguntas=(),
        campos=(),
        criterios_de_qualificacao=(),
        regras=(),
        ferramentas=(),
    )


class Empresa(Agregado):
    id: UUID | None
    tenant_id: str
    nome: str
    status: StatusEmpresa
    telefone_notificacao: Telefone
    criado_em: datetime
    janela_de_resposta: float
    configuracoes: DadosEmpresa

    def __init__(
        self,
        tenant_id: str,
        nome: str,
        status: StatusEmpresa,
        telefone_notificacao: str,
        configuracao_ia: ConfiguracaoIA,
        regras_gerais: list[str],
        cidades_atendidas: list[str],
        estagios: list[str],
        playbook: Playbook | None = None,
        id: UUID | None = None,
        criado_em: datetime | None = None,
        janela_de_resposta: float = 10,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.nome = nome
        self.status = StatusEmpresa(status)
        self.telefone_notificacao = Telefone(telefone_notificacao)
        self.criado_em = criado_em or datetime.now()
        self.janela_de_resposta = janela_de_resposta
        self.configuracoes = DadosEmpresa(
            configuracao_ia=configuracao_ia,
            regras_gerais=[RegrasGerais(regra) for regra in regras_gerais],
            cidades_atendidas=[Cidade(cidade) for cidade in cidades_atendidas],
            estagios=[Estagio(estagio) for estagio in estagios],
            playbook=playbook or _playbook_padrao(),
        )

    @property
    def configuracao_ia(self) -> ConfiguracaoIA:
        return self.configuracoes.configuracao_ia

    @property
    def regras_gerais(self) -> list[RegrasGerais]:
        return self.configuracoes.regras_gerais

    @property
    def cidades_atendidas(self) -> list[Cidade]:
        return self.configuracoes.cidades_atendidas

    @property
    def estagios(self) -> list[Estagio]:
        return self.configuracoes.estagios

    @property
    def playbook(self) -> Playbook:
        return self.configuracoes.playbook

    def ativar(self):
        self.status = StatusEmpresa.ATIVA

    def desativar(self):
        self.status = StatusEmpresa.INATIVA

    def cidade_atendida(self, cidade: str) -> bool:
        return any(cidade.casefold() == c.casefold() for c in self.cidades_atendidas)

    def estagio_permitido(self, estagio: str) -> bool:
        return estagio in self.estagios

    def esta_ativa(self) -> bool:
        return self.status is StatusEmpresa.ATIVA

    def esta_em_horario_de_atendimento(self, agora: datetime) -> bool:
        return self.configuracao_ia.horario_atendimento_ia.contem(agora)

    def pode_atender(self, agora: datetime) -> bool:
        return self.esta_ativa() and self.esta_em_horario_de_atendimento(agora)
