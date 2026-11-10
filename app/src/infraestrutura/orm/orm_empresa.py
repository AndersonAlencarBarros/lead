from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, String, Table, TypeDecorator, Uuid

from dominio.agregados.empresa import DadosEmpresa, Empresa
from dominio.objetos_de_valor.empresa import (
    Cidade,
    ConfiguracaoIA,
    Estagio,
    Intervalo,
    RegrasGerais,
    StatusEmpresa,
    TomDaIA,
)
from infraestrutura.base import Base, mapper_registry
from infraestrutura.orm.tipos import EnumString


class DadosEmpresaType(TypeDecorator):
    """Serializa DadosEmpresa para a coluna JSON configuracoes."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: DadosEmpresa | None, dialect):
        if value is None:
            return None

        configuracao = value.configuracao_ia
        intervalo = configuracao.horario_atendimento_ia
        return {
            "configuracao_ia": {
                "tom": configuracao.tom.value,
                "pode_dizer_que_e_ia": configuracao.pode_dizer_que_e_ia,
                "nome_assistente": configuracao.nome_assistente,
                "horario_atendimento_ia": {
                    "horario_inicio": intervalo.horario_inicio.isoformat(),
                    "horario_fim": intervalo.horario_fim.isoformat(),
                },
            },
            "regras_gerais": [str(regra) for regra in value.regras_gerais],
            "cidades_atendidas": [str(cidade) for cidade in value.cidades_atendidas],
            "estagios": [str(estagio) for estagio in value.estagios],
        }

    def process_result_value(self, value: dict | None, dialect):
        if value is None:
            return None

        configuracao = value["configuracao_ia"]
        intervalo = configuracao["horario_atendimento_ia"]
        return DadosEmpresa(
            configuracao_ia=ConfiguracaoIA(
                tom=TomDaIA(configuracao["tom"]),
                pode_dizer_que_e_ia=configuracao["pode_dizer_que_e_ia"],
                nome_assistente=configuracao["nome_assistente"],
                horario_atendimento_ia=Intervalo(
                    horario_inicio=datetime.fromisoformat(intervalo["horario_inicio"]),
                    horario_fim=datetime.fromisoformat(intervalo["horario_fim"]),
                ),
            ),
            regras_gerais=[
                RegrasGerais(regra) for regra in value.get("regras_gerais", [])
            ],
            cidades_atendidas=[
                Cidade(cidade) for cidade in value.get("cidades_atendidas", [])
            ],
            estagios=[Estagio(estagio) for estagio in value.get("estagios", [])],
        )


empresas_tabela = Table(
    "empresas",
    Base.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True, default=uuid4),
    Column("tenant_id", String(255), unique=True, nullable=False),
    Column("nome", String(255), nullable=False),
    Column("status", EnumString(StatusEmpresa), nullable=False),
    Column("telefone_notificacao", String(20), nullable=False),
    Column("criado_em", DateTime, nullable=False, default=datetime.now),
    Column("janela_de_resposta", Float, nullable=False, default=10),
    Column("configuracoes", DadosEmpresaType, nullable=False),
)

mapper_registry.map_imperatively(Empresa, empresas_tabela)
