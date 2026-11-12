import asyncio
import sys
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR))

from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.empresa import (
    ConfiguracaoIA,
    Intervalo,
    StatusEmpresa,
    TomDaIA,
)
from dominio.regras_de_negocio.servico_ia import ProvedorLiteLLM
from dominio.regras_de_negocio.servico_ia.ferramentas import construir_ferramentas
from testes.apoio import playbook_solar


def empresa() -> Empresa:
    agora = datetime.now()
    return Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=StatusEmpresa.ATIVA,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.FORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=Intervalo(
                horario_inicio=agora.replace(hour=0, minute=0, second=0, microsecond=0),
                horario_fim=agora.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ),
            ),
        ),
        regras_gerais=["Seja breve"],
        cidades_atendidas=["São Paulo"],
        estagios=["novo"],
        playbook=playbook_solar(),
    )


async def main() -> None:
    provedor = ProvedorLiteLLM(
        modelo="ollama_chat/granite3.3:2b",
        api_base="http://localhost:11434",
        temperatura=0,
        timeout=180,
    )
    ferramentas = construir_ferramentas(empresa())
    resposta = await provedor.gerar_resposta(
        [
            {
                "role": "system",
                "content": (
                    "Antes de responder, avalie o lead e execute mover_estagio. "
                    "Use function calling."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Olá, meu nome é João, moro em São Paulo, o imóvel é próprio, "
                    "é uma casa e a conta de luz é de 400 reais. Quero financiar."
                ),
            },
        ],
        ferramentas,
    )
    print("modelo:", resposta.modelo)
    print("chamadas:", resposta.chamadas)
    print("conteudo:", repr(resposta.conteudo))


asyncio.run(main())
