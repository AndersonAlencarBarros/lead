import hashlib
import json
from datetime import datetime, time, timedelta
from typing import Any

from dominio.agregados.agendamento import Agendamento
from dominio.agregados.auditoria import Auditoria
from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.agregados.turno_ia import TurnoIA
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento
from dominio.objetos_de_valor.ferramenta import NomeFerramenta
from infraestrutura.session import Session
from repositorio.agendamento import (
    AgendamentoDominioRepositorio,
    AgendamentoLeituraRepositorio,
)
from repositorio.auditoria import (
    AuditoriaDominioRepositorio,
    AuditoriaLeituraRepositorio,
)
from repositorio.conversa import (
    ConversaDominioRepositorio,
    ConversaLeituraRepositorio,
)
from repositorio.lead import LeadDominioRepositorio, LeadLeituraRepositorio


class ExecutorFerramentas:
    """Valida, executa e audita ferramentas de um turno."""

    def __init__(
        self,
        empresa: Empresa,
        conversa_id,
        lead_id,
        simulacao: bool,
        turno: TurnoIA,
    ) -> None:
        self._empresa = empresa
        self._conversa_id = conversa_id
        self._lead_id = lead_id
        self._simulacao = simulacao
        self._turno = turno
        self._slots_consultados: set[str] = set()

    async def executar(self, chamada) -> dict[str, Any]:
        try:
            nome = NomeFerramenta(chamada.nome)
            argumentos = self._validar_argumentos(nome, chamada.argumentos)
        except (TypeError, ValueError) as exc:
            await self._auditar(
                ferramenta=chamada.nome,
                argumentos=chamada.argumentos,
                sucesso=False,
                erro=str(exc),
            )
            return {"erro": str(exc)}

        try:
            async with Session() as session:
                resultado = await self._despachar(nome, argumentos, session)
                await self._salvar_auditoria(
                    session,
                    ferramenta=nome.value,
                    argumentos=argumentos,
                    resultado=resultado,
                    sucesso=True,
                )
                await session.commit()
                return resultado
        except ValueError as exc:
            await self._auditar(
                ferramenta=nome.value,
                argumentos=argumentos,
                sucesso=False,
                erro=str(exc),
            )
            return {"erro": str(exc)}

    async def _despachar(
        self,
        nome: NomeFerramenta,
        argumentos: dict[str, Any],
        session,
    ) -> dict[str, Any]:
        match nome:
            case NomeFerramenta.ATUALIZAR_LEAD:
                return await self._atualizar_lead(argumentos, session)
            case NomeFerramenta.MOVER_ESTAGIO:
                return await self._mover_estagio(argumentos, session)
            case NomeFerramenta.NOTIFICAR_EQUIPE:
                return self._notificar_equipe(argumentos)
            case NomeFerramenta.TRANSFERIR_HUMANO:
                return await self._transferir_humano(argumentos, session)
            case NomeFerramenta.CONSULTAR_AGENDA:
                return await self._consultar_agenda(session)
            case NomeFerramenta.MARCAR_AGENDA:
                return await self._marcar_agenda(argumentos, session)

    async def _atualizar_lead(self, argumentos, session) -> dict[str, Any]:
        lead = await self._lead(session)
        lead.atualizar_dados(
            nome=argumentos.get("nome"),
            cidade=argumentos.get("cidade"),
        )
        await LeadDominioRepositorio(session).salvar(lead)
        return {"ok": True, **argumentos}

    async def _mover_estagio(self, argumentos, session) -> dict[str, Any]:
        estagio = argumentos["estagio"]
        if not self._empresa.estagio_permitido(estagio):
            raise ValueError("estagio_nao_permitido")

        lead = await self._lead(session)
        lead.mover_estagio(estagio)
        await LeadDominioRepositorio(session).salvar(lead)
        return {"ok": True, "estagio": estagio}

    def _notificar_equipe(self, argumentos) -> dict[str, Any]:
        return {
            "ok": True,
            "simulada": self._simulacao,
            "telefone": str(self._empresa.telefone_notificacao),
            "resumo": argumentos["resumo"],
        }

    async def _transferir_humano(self, argumentos, session) -> dict[str, Any]:
        conversa = await ConversaLeituraRepositorio(session).buscar_por_id(
            self._conversa_id
        )
        if conversa is None:
            raise ValueError("conversa_nao_encontrada")

        conversa.ativar_intervencao_humana()
        await ConversaDominioRepositorio(session).salvar(conversa)

        if self._empresa.estagio_permitido("Humano"):
            lead = await self._lead(session)
            lead.mover_estagio("Humano")
            await LeadDominioRepositorio(session).salvar(lead)

        return {"ok": True, "motivo": argumentos["motivo"]}

    async def _consultar_agenda(self, session) -> dict[str, Any]:
        agora = datetime.now()
        limite = agora + timedelta(days=10)
        ocupados = await AgendamentoLeituraRepositorio(
            session
        ).listar_por_empresa_entre(self._empresa.id, agora, limite)

        horarios_ocupados = {agendamento.horario_agendado for agendamento in ocupados}
        slots: list[str] = []
        dia = agora.date()

        while len(slots) < 6 and dia <= (agora + timedelta(days=14)).date():
            dia = dia + timedelta(days=1)
            if dia.weekday() >= 5:
                continue

            for hora in (time(9, 0), time(14, 0)):
                horario = datetime.combine(dia, hora)
                if horario <= agora or horario in horarios_ocupados:
                    continue
                slots.append(horario.isoformat())

        self._slots_consultados = set(slots)
        return {"horarios": slots}

    async def _marcar_agenda(self, argumentos, session) -> dict[str, Any]:
        horario = datetime.fromisoformat(argumentos["horario"])
        if horario.isoformat() not in self._slots_consultados:
            raise ValueError("horario_nao_consultado")

        lead = await self._lead(session)
        leitura = AgendamentoLeituraRepositorio(session)
        existente = await leitura.buscar_por_lead_e_horario(lead.id, horario)
        if existente is not None:
            return {
                "ok": True,
                "agendamento_id": str(existente.id),
                "horario": horario.isoformat(),
            }

        conversa = await ConversaLeituraRepositorio(session).buscar_por_id(
            self._conversa_id
        )
        if conversa is None:
            raise ValueError("conversa_nao_encontrada")

        agendamento = Agendamento(
            empresa_id=self._empresa.id,
            lead_id=lead.id,
            telefone=str(lead.telefone or conversa.telefone),
            horario_agendado=horario,
            status=StatusDoAgendamento.CONFIRMADO,
        )
        salvo = await AgendamentoDominioRepositorio(session).salvar(agendamento)
        return {
            "ok": True,
            "agendamento_id": str(salvo.id),
            "horario": horario.isoformat(),
        }

    async def _lead(self, session) -> Lead:
        lead = await LeadLeituraRepositorio(session).buscar_por_id(self._lead_id)
        if lead is None:
            raise ValueError("lead_nao_encontrado")
        return lead

    @staticmethod
    def _validar_argumentos(
        nome: NomeFerramenta,
        argumentos: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(argumentos, dict):
            raise TypeError("argumentos_invalidos")

        exigidos = {
            NomeFerramenta.ATUALIZAR_LEAD: (),
            NomeFerramenta.MOVER_ESTAGIO: ("estagio",),
            NomeFerramenta.NOTIFICAR_EQUIPE: ("resumo",),
            NomeFerramenta.TRANSFERIR_HUMANO: ("motivo",),
            NomeFerramenta.CONSULTAR_AGENDA: (),
            NomeFerramenta.MARCAR_AGENDA: ("horario",),
        }[nome]

        for chave in exigidos:
            valor = argumentos.get(chave)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"argumento_invalido:{chave}")

        validados = {chave: argumentos[chave] for chave in exigidos}

        if nome is NomeFerramenta.ATUALIZAR_LEAD:
            for chave in ("nome", "cidade"):
                valor = argumentos.get(chave)
                if valor is None:
                    continue
                if not isinstance(valor, str) or not valor.strip():
                    raise ValueError(f"argumento_invalido:{chave}")
                validados[chave] = valor.strip()

            if not validados:
                raise ValueError("argumento_invalido:nome_ou_cidade")

        return validados

    async def _auditar(
        self,
        ferramenta: str,
        argumentos: dict[str, Any],
        sucesso: bool,
        erro: str | None = None,
        resultado: dict[str, Any] | None = None,
    ) -> None:
        async with Session() as session:
            await self._salvar_auditoria(
                session,
                ferramenta=ferramenta,
                argumentos=argumentos,
                resultado=resultado,
                sucesso=sucesso,
                erro=erro,
            )
            await session.commit()

    async def _salvar_auditoria(
        self,
        session,
        ferramenta: str,
        argumentos: dict[str, Any],
        sucesso: bool,
        erro: str | None = None,
        resultado: dict[str, Any] | None = None,
    ) -> None:
        hash_argumentos = self._hash(argumentos)
        existente = await AuditoriaLeituraRepositorio(
            session
        ).buscar_por_turno_ferramenta_hash(
            self._turno.id,
            ferramenta,
            hash_argumentos,
        )
        if existente is not None:
            return

        auditoria = Auditoria(
            turno_id=self._turno.id,
            conversa_id=self._conversa_id,
            lead_id=self._lead_id,
            ferramenta=ferramenta,
            argumentos=argumentos,
            resultado=resultado,
            sucesso=sucesso,
            erro=erro,
            hash_argumentos=hash_argumentos,
        )
        await AuditoriaDominioRepositorio(session).salvar(auditoria)

    @staticmethod
    def _hash(argumentos: dict[str, Any]) -> str:
        conteudo = json.dumps(
            argumentos,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
