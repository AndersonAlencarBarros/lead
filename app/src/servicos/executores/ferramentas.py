import hashlib
import json
from datetime import datetime, time, timedelta
from typing import Any

from dominio.agregados.acao_executada import AcaoExecutada
from dominio.agregados.agendamento import Agendamento
from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.agregados.turno_ia import TurnoIA
from dominio.objetos_de_valor.agendamento import StatusDoAgendamento
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.objetos_de_valor.ferramenta import NomeFerramenta
from dominio.objetos_de_valor.playbook import CampoDaFicha, TipoCampo
from infraestrutura.session import Session
from repositorio.acao_executada import (
    AcaoDominioRepositorio,
    AcaoLeituraRepositorio,
)
from repositorio.agendamento import (
    AgendamentoDominioRepositorio,
    AgendamentoLeituraRepositorio,
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
        mensagens_pendentes: list[Mensagem],
        simulacao: bool,
        turno: TurnoIA,
    ) -> None:
        self._empresa = empresa
        self._conversa_id = conversa_id
        self._lead_id = lead_id
        self._mensagens_pendentes = mensagens_pendentes
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
            case NomeFerramenta.ADICIONAR_TAG:
                return await self._adicionar_tag(argumentos, session)
            case NomeFerramenta.MOVER_ESTAGIO:
                return await self._mover_estagio(argumentos, session)
            case NomeFerramenta.ATUALIZAR_FICHA:
                return await self._atualizar_ficha(argumentos, session)
            case NomeFerramenta.NOTIFICAR_EQUIPE:
                return self._notificar_equipe(argumentos)
            case NomeFerramenta.TRANSFERIR_HUMANO:
                return await self._transferir_humano(argumentos, session)
            case NomeFerramenta.CONSULTAR_AGENDA:
                return await self._consultar_agenda(session)
            case NomeFerramenta.MARCAR_AGENDA:
                return await self._marcar_agenda(argumentos, session)

    async def _adicionar_tag(self, argumentos, session) -> dict[str, Any]:
        lead = await self._lead(session)
        lead.adicionar_tag(argumentos["tag"])
        await LeadDominioRepositorio(session).salvar(lead)
        return {"ok": True, "tag": argumentos["tag"]}

    async def _mover_estagio(self, argumentos, session) -> dict[str, Any]:
        estagio = argumentos["estagio"]
        if not self._empresa.estagio_permitido(estagio):
            raise ValueError("estagio_nao_permitido")

        lead = await self._lead(session)
        lead.mover_estagio(estagio)
        await LeadDominioRepositorio(session).salvar(lead)
        return {"ok": True, "estagio": estagio}

    async def _atualizar_ficha(self, argumentos, session) -> dict[str, Any]:
        campo = self._empresa.playbook.campo(argumentos["campo"])
        if campo is None:
            raise ValueError("campo_nao_permitido")

        self._validar_evidencia(argumentos["evidencia"])
        valor = self._validar_valor(campo, argumentos["valor"])

        lead = await self._lead(session)
        lead.atualizar_ficha(campo.nome, valor)
        await LeadDominioRepositorio(session).salvar(lead)
        return {"ok": True, "campo": campo.nome, "valor": valor}

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

    def _validar_evidencia(self, evidencia: str) -> None:
        alvo = self._normalizar(evidencia)
        fontes = [
            self._normalizar(mensagem.texto)
            for mensagem in self._mensagens_pendentes
            if mensagem.foi_respondida_pelo_usuario
        ]
        if not any(alvo in fonte for fonte in fontes):
            raise ValueError("evidencia_nao_encontrada")

    @staticmethod
    def _normalizar(texto: str) -> str:
        return " ".join(texto.casefold().split())

    @staticmethod
    def _validar_valor(campo: CampoDaFicha, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("valor_vazio")

        if campo.tipo is TipoCampo.OPCAO and limpo not in campo.opcoes:
            raise ValueError("valor_fora_das_opcoes")

        if campo.tipo is TipoCampo.NUMERO:
            try:
                return str(float(limpo.replace(",", ".")))
            except ValueError as exc:
                raise ValueError("valor_numerico_invalido") from exc

        if campo.tipo is TipoCampo.DATA:
            try:
                datetime.fromisoformat(limpo)
            except ValueError as exc:
                raise ValueError("valor_data_invalido") from exc

        return limpo

    @staticmethod
    def _validar_argumentos(
        nome: NomeFerramenta,
        argumentos: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(argumentos, dict):
            raise TypeError("argumentos_invalidos")

        exigidos = {
            NomeFerramenta.ADICIONAR_TAG: ("tag",),
            NomeFerramenta.MOVER_ESTAGIO: ("estagio",),
            NomeFerramenta.ATUALIZAR_FICHA: ("campo", "valor", "evidencia"),
            NomeFerramenta.NOTIFICAR_EQUIPE: ("resumo",),
            NomeFerramenta.TRANSFERIR_HUMANO: ("motivo",),
            NomeFerramenta.CONSULTAR_AGENDA: (),
            NomeFerramenta.MARCAR_AGENDA: ("horario",),
        }[nome]

        for chave in exigidos:
            valor = argumentos.get(chave)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"argumento_invalido:{chave}")

        return {chave: argumentos[chave] for chave in exigidos}

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
        existente = await AcaoLeituraRepositorio(
            session
        ).buscar_por_turno_ferramenta_hash(
            self._turno.id,
            ferramenta,
            hash_argumentos,
        )
        if existente is not None:
            return

        acao = AcaoExecutada(
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
        await AcaoDominioRepositorio(session).salvar(acao)

    @staticmethod
    def _hash(argumentos: dict[str, Any]) -> str:
        conteudo = json.dumps(
            argumentos,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
