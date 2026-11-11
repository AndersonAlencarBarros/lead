from fastapi import status
from fastapi.exceptions import HTTPException


class RespostaDoUsuario(HTTPException):
    """Exceção base para erros comunicados ao usuário.

    Herda de HTTPException para integração nativa com FastAPI,
    dispensando handlers customizados.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Erro na requisição."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=self.__class__.status_code,
            detail=detail or self.__class__.detail,
        )


class EmpresaJaCadastrada(RespostaDoUsuario):
    status_code = status.HTTP_409_CONFLICT
    detail = "Empresa já cadastrada para este tenant"


class LeadJaCadastrado(RespostaDoUsuario):
    status_code = status.HTTP_409_CONFLICT
    detail = "Lead já cadastrado para esta empresa e telefone"


class LeadNaoEncontrado(RespostaDoUsuario):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Lead não encontrado"


class AgendamentoNaoEncontrado(RespostaDoUsuario):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Agendamento não encontrado"


class ConversaNaoEncontrada(RespostaDoUsuario):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Conversa não encontrada"


class FalhaAoConsultarIA(RespostaDoUsuario):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Serviço de IA indisponível"


class FilaDeProcessamentoIndisponivel(RespostaDoUsuario):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Fila de processamento indisponível"
