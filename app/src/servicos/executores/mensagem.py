from infraestrutura import UnidadeDeTrabalho
from servicos.serializadores.conversacao import MensagemSerializador


def adicionar_tag():
    ...


def mover_estagio():
    ...


def atualizar_ficha(
    db,
    lead_id: int,
    campo: str,
    valor: str
):
    campos_permitidos = {
        "nome",
        "cidade",
        "tipo_imovel",
        "situacao_imovel",
        "valor_conta",
        "forma_pagamento"
    }

    if campo not in campos_permitidos:
        raise ValueError("Campo não permitido")

    db.execute(
        f"UPDATE leads SET {campo} = ? WHERE id = ?",
        (valor, lead_id)
    )

    db.commit()

    return {
        "sucesso": True,
        "campo": campo,
        "valor": valor
    }

def notificar_equipe():
    ...


def transferir_humano():
    ...


def consultar_agenda():
    ...


def marcar_agenda():
    ...

async def receber_mensagem(mensagem: MensagemSerializador, uow: UnidadeDeTrabalho):
    # consultar mensagem_id
    # valida se é duplicada
    # se nao existir mensagem nova
    # busca tenant da empresa
    #

    """Valida, persiste o agregado Usuario via UoW e gerencia commit/rollback e erros."""
    # existente = await uow.leitura.buscar_por_email(mensagem.email)
    # if existente is not None:
    #     raise EmailJaCadastrado()
    #
    # novo_usuario = UsuarioDominio(
    #     nome=payload.name,
    #     email=payload.email,
    #     cpf=payload.cpf,
    # )
    #
    # try:
    #     salvo = await uow.dominio.salvar(novo_usuario)
    #     assert salvo.id is not None
    #     await uow.commit()
    #     return salvo
    # except IntegrityError:
    #     await uow.rollback()
    #     raise EmailJaCadastrado()
