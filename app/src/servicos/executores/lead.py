from uuid import UUID

from sqlalchemy.exc import IntegrityError

from dominio.agregados.lead import Lead
from exceptions import LeadJaCadastrado, LeadNaoEncontrado
from infraestrutura import UnidadeDeTrabalho
from repositorio.lead import LeadDominioRepositorio, LeadLeituraRepositorio


async def criar_lead(
    empresa_id: UUID,
    uow: UnidadeDeTrabalho,
    nome: str | None = None,
    telefone: str | None = None,
    cidade: str | None = None,
    estagio: str | None = None,
    tags: list[str] | None = None,
    ficha: dict[str, str] | None = None,
) -> Lead:
    repo_dominio: LeadDominioRepositorio = uow.dominio
    repo_leitura: LeadLeituraRepositorio = uow.leitura

    if telefone is not None:
        existente = await repo_leitura.buscar_por_empresa_e_telefone(
            empresa_id, telefone
        )
        if existente is not None:
            raise LeadJaCadastrado()

    lead = Lead(
        empresa_id=empresa_id,
        nome=nome,
        telefone=telefone,
        cidade=cidade,
        estagio=estagio,
        tags=tags,
        ficha=ficha,
    )

    try:
        return await repo_dominio.salvar(lead)
    except IntegrityError as exc:
        raise LeadJaCadastrado() from exc


async def buscar_lead(lead_id: UUID, uow: UnidadeDeTrabalho) -> Lead:
    repo_leitura: LeadLeituraRepositorio = uow.leitura
    lead = await repo_leitura.buscar_por_id(lead_id)
    if lead is None:
        raise LeadNaoEncontrado()
    return lead
