from typing import Any

from dominio.agregados.empresa import Empresa


def construir_ferramentas(empresa: Empresa) -> list[dict[str, Any]]:
    ferramentas = [
        {
            "type": "function",
            "function": {
                "name": "atualizar_lead",
                "description": (
                    "Registra o nome ou a cidade confirmados pelo lead."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "cidade": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mover_estagio",
                "description": (
                    "Move o lead no funil conforme os critérios de qualificação."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estagio": {
                            "type": "string",
                            "enum": [str(estagio) for estagio in empresa.estagios],
                        }
                    },
                    "required": ["estagio"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "notificar_equipe",
                "description": "Notifica a equipe com resumo do lead.",
                "parameters": {
                    "type": "object",
                    "properties": {"resumo": {"type": "string"}},
                    "required": ["resumo"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "transferir_humano",
                "description": "Passa o atendimento para um humano.",
                "parameters": {
                    "type": "object",
                    "properties": {"motivo": {"type": "string"}},
                    "required": ["motivo"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "consultar_agenda",
                "description": "Retorna horarios livres.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "marcar_agenda",
                "description": "Agenda horario retornado por consultar_agenda.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "horario": {
                            "type": "string",
                            "format": "date-time",
                        }
                    },
                    "required": ["horario"],
                    "additionalProperties": False,
                },
            },
        },
    ]

    permitidas = {ferramenta.value for ferramenta in empresa.playbook.ferramentas}
    return [
        ferramenta
        for ferramenta in ferramentas
        if ferramenta["function"]["name"] in permitidas
    ]
