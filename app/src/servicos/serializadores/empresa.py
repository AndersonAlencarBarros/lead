from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dominio.objetos_de_valor.empresa import StatusEmpresa, TomDaIA
from dominio.objetos_de_valor.ferramenta import NomeFerramenta


class IntervaloSerializador(BaseModel):
    horario_inicio: datetime
    horario_fim: datetime

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.horario_inicio >= self.horario_fim:
            raise ValueError("horario_inicio deve ser anterior a horario_fim")
        return self


class ConfiguracaoIASerializador(BaseModel):
    tom: TomDaIA
    pode_dizer_que_e_ia: bool
    nome_assistente: str
    horario_atendimento_ia: IntervaloSerializador


class PlaybookSerializador(BaseModel):
    nome: str = Field(min_length=1)
    versao: int = Field(default=1, ge=1)
    objetivo: str = Field(min_length=1)
    perguntas: list[str] = Field(min_length=1)
    criterios_de_qualificacao: list[str] = Field(default_factory=list)
    regras: list[str] = Field(default_factory=list)
    ferramentas: list[NomeFerramenta] = Field(min_length=1)

    model_config = ConfigDict(from_attributes=True)


EXEMPLO_PLAYBOOK_SOL_NASCENTE = {
    "nome": "energia-solar-residencial",
    "versao": 1,
    "objetivo": "Qualificar lead e agendar visita técnica.",
    "perguntas": [
        "Qual o nome e a cidade?",
        "O imóvel é próprio ou alugado?",
        "É casa ou apartamento?",
        "Qual o valor médio da conta de luz?",
        "Tem interesse em financiar o sistema de energia solar ou prefere pagar à vista?",
    ],
    "criterios_de_qualificacao": [
        "Imóvel próprio, casa, conta acima de R$ 250 e cidade atendida."
    ],
    "regras": [
        "Nunca prometer economia exata.",
        "Nunca informar preço final.",
    ],
    "ferramentas": [
        "atualizar_lead",
        "mover_estagio",
        "notificar_equipe",
        "transferir_humano",
        "consultar_agenda",
        "marcar_agenda",
    ],
}


EXEMPLO_EMPRESA_SOL_NASCENTE = {
    "tenant_id": "sol-nascente",
    "nome": "Sol Nascente Energia Solar",
    "status": "ativa",
    "telefone_notificacao": "5581988887777",
    "janela_de_resposta": 8,
    "configuracao_ia": {
        "tom": "informal",
        "pode_dizer_que_e_ia": True,
        "nome_assistente": "Luz",
        "horario_atendimento_ia": {
            "horario_inicio": "2026-01-01T00:00:00",
            "horario_fim": "2026-01-01T23:59:59",
        },
    },
    "regras_gerais": [
        "Nunca prometer valor exato de economia; dizer que depende da visita técnica.",
        "Nunca informar preço final; dizer que o consultor apresenta o orçamento.",
        "Não pedir nem repetir senhas ou dados bancários.",
        "Se o lead disser que já é cliente, transferir para humano.",
    ],
    "cidades_atendidas": [
        "Recife",
        "Olinda",
        "Jaboatão dos Guararapes",
        "Caruaru",
    ],
    "estagios": [
        "Novo",
        "Qualificacao",
        "Qualificado",
        "Desqualificado",
        "Agendado",
        "Humano",
    ],
    "playbook": EXEMPLO_PLAYBOOK_SOL_NASCENTE,
}


EXEMPLO_PLAYBOOK_CONFEITARIA = {
    "nome": "confeitaria-sob-encomenda",
    "versao": 1,
    "objetivo": "Qualificar encomenda e confirmar data.",
    "perguntas": [
        "Qual o nome e a cidade?",
        "Qual produto, sabor e quantidade?",
        "Qual a data do evento?",
        "A entrega é para retirada ou delivery?",
    ],
    "criterios_de_qualificacao": [
        "Data futura, quantidade mínima de 20 unidades e cidade atendida."
    ],
    "regras": [
        "Nunca confirmar preço final sem consultor.",
        "Confirmar sabor e recheio antes de fechar a encomenda.",
        "Não pedir nem repetir dados bancários.",
    ],
    "ferramentas": [
        "atualizar_lead",
        "mover_estagio",
        "notificar_equipe",
        "transferir_humano",
        "consultar_agenda",
        "marcar_agenda",
    ],
}


EXEMPLO_EMPRESA_CONFEITARIA = {
    "tenant_id": "confeitaria-encanto",
    "nome": "Confeitaria Encanto",
    "status": "ativa",
    "telefone_notificacao": "5581977776666",
    "janela_de_resposta": 5,
    "configuracao_ia": {
        "tom": "formal",
        "pode_dizer_que_e_ia": False,
        "nome_assistente": "Doce",
        "horario_atendimento_ia": {
            "horario_inicio": "2026-01-01T00:00:00",
            "horario_fim": "2026-01-01T23:59:59",
        },
    },
    "regras_gerais": [
        "Nunca confirmar preço final; o consultor apresenta o orçamento.",
        "Não pedir nem repetir senhas ou dados bancários.",
        "Se o lead disser que já é cliente, transferir para humano.",
    ],
    "cidades_atendidas": [
        "Recife",
        "Olinda",
        "Jaboatão dos Guararapes",
    ],
    "estagios": [
        "Novo",
        "Qualificacao",
        "Qualificado",
        "Desqualificado",
        "Agendado",
        "Humano",
    ],
    "playbook": EXEMPLO_PLAYBOOK_CONFEITARIA,
}


class EmpresaCriacaoSerializador(BaseModel):
    tenant_id: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    status: StatusEmpresa = StatusEmpresa.ATIVA
    telefone_notificacao: str = Field(min_length=1)
    janela_de_resposta: float = Field(default=10, gt=0)
    configuracao_ia: ConfiguracaoIASerializador
    regras_gerais: list[str] = Field(default_factory=list)
    cidades_atendidas: list[str] = Field(default_factory=list)
    estagios: list[str] = Field(default_factory=list)
    playbook: PlaybookSerializador

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                EXEMPLO_EMPRESA_SOL_NASCENTE,
                EXEMPLO_EMPRESA_CONFEITARIA,
            ]
        }
    )


class EmpresaResposta(BaseModel):
    id: UUID
    tenant_id: str
    nome: str
    status: StatusEmpresa
    telefone_notificacao: str
    criado_em: datetime
    janela_de_resposta: float
    configuracao_ia: ConfiguracaoIASerializador
    regras_gerais: list[str]
    cidades_atendidas: list[str]
    estagios: list[str]
    playbook: PlaybookSerializador

    model_config = ConfigDict(from_attributes=True)
