from sqlalchemy.exc import IntegrityError

from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.empresa import ConfiguracaoIA, Intervalo
from dominio.objetos_de_valor.playbook import CampoDaFicha, Playbook, TipoCampo
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
    playbook = Playbook(
        nome=payload.playbook.nome,
        versao=payload.playbook.versao,
        objetivo=payload.playbook.objetivo,
        perguntas=tuple(payload.playbook.perguntas),
        campos=tuple(
            CampoDaFicha(
                nome=campo.nome,
                descricao=campo.descricao,
                tipo=TipoCampo(campo.tipo),
                opcoes=tuple(campo.opcoes),
                obrigatorio=campo.obrigatorio,
            )
            for campo in payload.playbook.campos
        ),
        criterios_de_qualificacao=tuple(payload.playbook.criterios_de_qualificacao),
        regras=tuple(payload.playbook.regras),
        ferramentas=tuple(payload.playbook.ferramentas),
    )
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
        playbook=playbook,
        janela_de_resposta=payload.janela_de_resposta,
    )

    try:
        return await repo_dominio.salvar(empresa)
    except IntegrityError as exc:
        raise EmpresaJaCadastrada() from exc
