from typing import Any

from dominio.agregados.empresa import Empresa


def construir_ferramentas(empresa: Empresa) -> list[dict[str, Any]]:
    playbook = empresa.playbook

    ferramentas = [
        {
            "type": "function",
            "function": {
                "name": "adicionar_tag",
                "description": "Marca o lead com uma tag.",
                "parameters": {
                    "type": "object",
                    "properties": {"tag": {"type": "string"}},
                    "required": ["tag"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mover_estagio",
                "description": "Move o lead no funil.",
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
                "name": "atualizar_ficha",
                "description": (
                    "Grava dado dito pelo lead. "
                    "A evidencia precisa ser trecho literal do lead."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campo": {
                            "type": "string",
                            "enum": [campo.nome for campo in playbook.campos],
                        },
                        "valor": {"type": "string"},
                        "evidencia": {"type": "string"},
                    },
                    "required": ["campo", "valor", "evidencia"],
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

    permitidas = {ferramenta.value for ferramenta in playbook.ferramentas}
    return [
        ferramenta
        for ferramenta in ferramentas
        if ferramenta["function"]["name"] in permitidas
    ]
