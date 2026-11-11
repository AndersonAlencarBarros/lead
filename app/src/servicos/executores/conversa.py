from datetime import datetime

from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import Mensagem, ResultadoMensagem
from dominio.regras_de_negocio.conversa import (
    _mensagens_na_janela_de_resposta,
    _pode_responder,
    _salvar_resposta_ia,
    idempotente_em_conflito,
)
from dominio.regras_de_negocio.servico_ia import ServicoIA
from infraestrutura import Dominio, UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio, ConversaLeituraRepositorio
from servicos.serializadores.conversacao import MensagemSerializador


def adicionar_tag(): ...


def mover_estagio(): ...


def atualizar_ficha(db, lead_id: int, campo: str, valor: str):
    campos_permitidos = {
        "nome",
        "cidade",
        "tipo_imovel",
        "situacao_imovel",
        "valor_conta",
        "forma_pagamento",
    }

    if campo not in campos_permitidos:
        raise ValueError("Campo não permitido")

    db.execute(f"UPDATE leads SET {campo} = ? WHERE id = ?", (valor, lead_id))

    db.commit()

    return {"sucesso": True, "campo": campo, "valor": valor}


def notificar_equipe(): ...


def transferir_humano(): ...


def consultar_agenda(): ...


def marcar_agenda(): ...


@idempotente_em_conflito
async def receber_mensagem(
    mensagem: MensagemSerializador, uow: UnidadeDeTrabalho
) -> ResultadoMensagem:
    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    if await repo_leitura.mensagem_existe(mensagem.message_id):
        return ResultadoMensagem.DUPLICADA

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

    # Adiciona uma mensagem a conversa
    conversa.receber_mensagem(
        Mensagem(
            id=None,
            identificador_da_mensagem=mensagem.message_id,
            conversa_id=None,
            texto=mensagem.texto,
            foi_enviada_pela_ia=False,
            foi_enviada_pelo_humano=False,
            criado_em=datetime.now(),
        )
    )

    await repo_dominio.salvar(conversa)
    return ResultadoMensagem.PROCESSADA


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
        if empresa is None:
            return False

        conversa = await uow.dominio.buscar_por_empresa_e_telefone(tenant_id, telefone)
        if conversa is None:
            return False

        mensagens_recentes = _mensagens_na_janela_de_resposta(
            conversa,
            empresa.janela_de_resposta,
            datetime.now(),
        )
        if not mensagens_recentes or not _pode_responder(conversa):
            return False

        texto = await servico_ia.responder(mensagens_recentes, empresa)

        return await _salvar_resposta_ia(
            conversa,
            mensagem_id,
            texto,
            uow,
        )
