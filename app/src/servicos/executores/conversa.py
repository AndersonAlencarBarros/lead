from datetime import datetime

from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import (
    AcaoIntervencao,
    AutorMensagem,
    Mensagem,
    ResultadoMensagem,
)
from dominio.regras_de_negocio.conversa import (
    MENSAGEM_FORA_DO_HORARIO,
    _salvar_resposta_ia,
    contexto_para_resposta_da_ia,
    idempotente_em_conflito,
    ultima_mensagem_de_intervencao_humana,
    ultima_resposta_da_ia,
)
from dominio.regras_de_negocio.servico_ia import ServicoIA
from exceptions import (
    ConversaNaoEncontrada,
    FilaDeProcessamentoIndisponivel,
    IntervencaoHumanaNaoEncontrada,
    RespostaDaIANaoEncontrada,
)
from infraestrutura import Dominio, UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio, ConversaLeituraRepositorio
from servicos.serializadores.conversacao import (
    IntervencaoSerializador,
    MensagemSerializador,
)
from servicos.visualizadores.conversa import (
    buscar_conversa_por_empresa_e_telefone,
)


@idempotente_em_conflito
async def receber_mensagem(
    mensagem: MensagemSerializador, uow: UnidadeDeTrabalho
) -> ResultadoMensagem:
    from dominio.regras_de_negocio.servico_ia.responder_conversa import (
        criar_resposta_da_ia,
    )

    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    if await repo_leitura.mensagem_existe(mensagem.message_id):
        return ResultadoMensagem.DUPLICADA

    empresa = await repo_dominio.buscar_empresa_por_tenant_id(mensagem.tenant_id)
    atraso = empresa.janela_de_resposta if empresa is not None else 0

    # Busca se existe conversa
    conversa = await repo_leitura.buscar_por_empresa_e_telefone(
        mensagem.tenant_id, mensagem.telefone
    )
    if conversa is None:
        # Inicia-se uma conversa
        conversa = Conversa(
            tenant_id=mensagem.tenant_id,
            lead_id=None,
            telefone=mensagem.telefone,
        )

    eh_humano = mensagem.autor is AutorMensagem.HUMANO

    # Adiciona uma mensagem a conversa
    conversa.receber_mensagem(
        Mensagem(
            id=None,
            identificador_da_mensagem=mensagem.message_id,
            conversa_id=None,
            texto=mensagem.texto,
            foi_gerada_pela_ia=False,
            foi_respondida_pelo_usuario=not eh_humano,
            foi_intervencao_humana=eh_humano,
            criado_em=datetime.now(),
        )
    )

    if eh_humano:
        conversa.ativar_intervencao_humana()

    await repo_dominio.salvar(conversa)
    await uow.commit()

    if conversa.ia_pode_responder():
        try:
            criar_resposta_da_ia(
                mensagem.tenant_id,
                mensagem.telefone,
                mensagem.message_id,
                atraso,
            )
        except Exception as exc:
            raise FilaDeProcessamentoIndisponivel() from exc

    return ResultadoMensagem.PROCESSADA


def _ultima_mensagem_do_usuario_sem_resposta(
    conversa: Conversa,
) -> Mensagem | None:
    """Última mensagem do lead posterior à última resposta da IA."""
    ultima_ia = ultima_resposta_da_ia(conversa)
    limite = ultima_ia.criado_em if ultima_ia is not None else None

    candidatas = [
        mensagem
        for mensagem in conversa.mensagens
        if mensagem.foi_respondida_pelo_usuario
        and (limite is None or mensagem.criado_em > limite)
    ]
    return max(candidatas, key=lambda mensagem: mensagem.criado_em, default=None)


async def alterar_intervencao(
    payload: IntervencaoSerializador,
    uow: UnidadeDeTrabalho,
) -> Conversa:
    """Assume a conversa ou devolve o atendimento para a IA."""
    from dominio.regras_de_negocio.servico_ia.responder_conversa import (
        criar_resposta_da_ia,
    )

    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    conversa = await repo_leitura.buscar_por_empresa_e_telefone(
        payload.tenant_id,
        payload.telefone,
    )
    if conversa is None:
        raise ConversaNaoEncontrada()

    if payload.acao is AcaoIntervencao.ASSUMIR:
        conversa.ativar_intervencao_humana()
        return await repo_dominio.salvar(conversa)

    conversa.desativar_intervencao_humana()
    await repo_dominio.salvar(conversa)
    await uow.commit()

    mensagem_pendente = _ultima_mensagem_do_usuario_sem_resposta(conversa)
    if mensagem_pendente is not None:
        try:
            criar_resposta_da_ia(
                conversa.tenant_id,
                str(conversa.telefone),
                mensagem_pendente.identificador_da_mensagem,
            )
        except Exception as exc:
            raise FilaDeProcessamentoIndisponivel() from exc

    return conversa


async def responder_ultima_mensagem_da_conversa(
    tenant_id: str,
    telefone: str,
    uow: UnidadeDeTrabalho,
) -> tuple[Conversa, Mensagem]:
    """Busca a conversa e a última mensagem relevante para o usuário."""
    conversa = await buscar_conversa_por_empresa_e_telefone(
        tenant_id,
        telefone,
        uow,
    )
    if conversa is None:
        raise ConversaNaoEncontrada()

    if conversa.teve_intervencao_humana:
        mensagem = ultima_mensagem_de_intervencao_humana(conversa)
        if mensagem is None:
            raise IntervencaoHumanaNaoEncontrada()
    else:
        mensagem = ultima_resposta_da_ia(conversa)
        if mensagem is None:
            raise RespostaDaIANaoEncontrada()

    return conversa, mensagem


async def responder_conversa(
    tenant_id: str,
    telefone: str,
    mensagem_id: str,
    servico_ia: ServicoIA,
) -> bool:
    """Gera e persiste a resposta da IA para a mensagem informada."""

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        empresa: Empresa | None = await uow.dominio.buscar_empresa_por_tenant_id(
            tenant_id
        )
        if empresa is None or not empresa.esta_ativa():
            return False

        conversa = await uow.dominio.buscar_por_empresa_e_telefone(tenant_id, telefone)
        if conversa is None:
            return False

        ultima_do_lead = conversa.ultima_mensagem_do_lead()
        if (
            ultima_do_lead is None
            or ultima_do_lead.identificador_da_mensagem != mensagem_id
        ):
            return False

        if not empresa.esta_em_horario_de_atendimento(datetime.now()):
            texto = MENSAGEM_FORA_DO_HORARIO.format(
                horario=empresa.configuracao_ia.horario_atendimento_ia.formatar()
            )
            return await _salvar_resposta_ia(
                conversa,
                mensagem_id,
                texto,
                uow,
            )

        mensagens_contexto = contexto_para_resposta_da_ia(conversa)
        if mensagens_contexto is None:
            return False

        texto = await servico_ia.responder(mensagens_contexto, empresa)

        return await _salvar_resposta_ia(
            conversa,
            mensagem_id,
            texto,
            uow,
        )
