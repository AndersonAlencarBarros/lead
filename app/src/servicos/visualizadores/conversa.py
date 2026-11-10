from dominio.agregados.conversa import Conversa
from infraestrutura.unidade_de_trabalho import UnidadeDeTrabalho
from repositorio.conversa import ConversaLeituraRepositorio


async def buscar_conversa_por_empresa_e_telefone(
    empresa_id: str,
    telefone: str,
    uow: UnidadeDeTrabalho,
) -> Conversa | None:
    repo_leitura: ConversaLeituraRepositorio = uow.leitura
    return await repo_leitura.buscar_por_empresa_e_telefone(empresa_id, telefone)
