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


class EmailJaCadastrado(RespostaDoUsuario):
    """Disparada quando o e-mail informado já existe na base de dados."""

    status_code = status.HTTP_409_CONFLICT
    detail = "Email já cadastrado"

class ConversaNaoEncontrada(RespostaDoUsuario):

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Conversa não encontrada"

