from sqlalchemy.exc import IntegrityError

from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.empresa import ConfiguracaoIA, Intervalo
from exceptions import EmpresaJaCadastrada
from infraestrutura import UnidadeDeTrabalho
from repositorio.empresa import EmpresaDominioRepositorio, EmpresaLeituraRepositorio
from servicos.serializadores.empresa import EmpresaCriacaoSerializador


async def criar_empresa(
    payload: EmpresaCriacaoSerializador,
    uow: UnidadeDeTrabalho,
) -> Empresa:
    repo_dominio: EmpresaDominioRepositorio = uow.dominio
    repo_leitura: EmpresaLeituraRepositorio = uow.leitura

    if await repo_leitura.buscar_por_tenant_id(payload.tenant_id) is not None:
        raise EmpresaJaCadastrada()

    configuracao = payload.configuracao_ia
    empresa = Empresa(
        tenant_id=payload.tenant_id,
        nome=payload.nome,
        status=payload.status,
        telefone_notificacao=payload.telefone_notificacao,
        configuracao_ia=ConfiguracaoIA(
            tom=configuracao.tom,
            pode_dizer_que_e_ia=configuracao.pode_dizer_que_e_ia,
            nome_assistente=configuracao.nome_assistente,
            horario_atendimento_ia=Intervalo(
                horario_inicio=configuracao.horario_atendimento_ia.horario_inicio,
                horario_fim=configuracao.horario_atendimento_ia.horario_fim,
            ),
        ),
        regras_gerais=payload.regras_gerais,
        cidades_atendidas=payload.cidades_atendidas,
        estagios=payload.estagios,
        janela_de_resposta=payload.janela_de_resposta,
    )

    try:
        return await repo_dominio.salvar(empresa)
    except IntegrityError as exc:
        raise EmpresaJaCadastrada() from exc
