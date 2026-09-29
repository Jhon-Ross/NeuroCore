# ============================================================================
# MODULO: orchestrator.py
# ORQUESTRADOR LANGGRAPH CORE — NUCLEO DO NEUROCORE
#
# Este é o CÉREBRO do cérebro. Tudo passa por aqui.
#
# Arquitetura mínima DIA 1 (LangGraph state machine, SEM LangChain):
#
#   [USUARIO] → prompt →  [Orquestrador]
#                              │
#                              ▼
#               ┌─ HybridRouter (decide LOCAL vs API)
#               │
#               └─► chama Especialista via BaseSpecialist.infer()
#                              │
#                              ▼
#               ┌─ resultado → grava no SQLite (historico)
#               │           → registra XP no RPG (cortex_geral)
#               └─► retorna p/ usuário + painel
#
# No Dia 1 só temos 1 ferramenta REAL: chamar_cortex_geral → llm_core.
# As outras 6 regiões vão sendo plugadas à medida que suas fases chegarem.
# ============================================================================

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypedDict

# LangGraph Core (state machine)
from langgraph.graph import StateGraph, END

from core.base_specialist import BaseSpecialist, ResultadoInferencia
from core.hybrid_router import (
    HybridRouter,
    RoteamentoDestino,
    hybrid_router as _router_default,
)
from core.logger import log
from core.memory_manager import GerenciadorMemoria, memoria as _mem_default
from core.progress_rpg import GerenciadorRPG, rpg as _rpg_default
from core.vram_manager import VramManager, vram_manager as _vram_default

from specialists import REGIOES_CEREBRAIS
from specialists.llm_core import EspecialistaLlmCore


# ============================================================================
# Schema do estado do LangGraph (TypedDict = imutavel entre nos)
# ============================================================================

class EstadoGrafo(TypedDict, total=False):
    """Tudo que o LangGraph carrega de um nó pro outro."""
    # Entrada do usuário
    pergunta_usuario: str
    session_id: int
    habilidade_alvo: str               # "cortex_geral", "codigo", etc
    historico_chat: List[Dict[str, str]]   # [{role,content}]

    # Decisao do roteador
    roteamento_destino: str            # "local" / "api_ext"
    roteamento_modelo: str

    # Inferencia
    resultado_inferencia: Optional[Dict[str, Any]]   # serializado ResultadoInferencia
    resposta_texto: str
    sucesso: bool
    tempo_total_ms: float

    # Meta-dados pós-inferencia
    xp_ganho: int
    novo_feito_id: Optional[int]


# ============================================================================
# Prompt de sistema permanente do Prometeu
# ============================================================================

SYSTEM_PROMPT_PROMETEU = """\
Você é o PROMETEU, um cérebro de IA pessoal 100% local rodando no computador \
do Jhon Ross no Windows com GPU AMD RX 7600.

REGRAS OBRIGATÓRIAS DE PERSONALIDADE:
1. Responda SEMPRE em PORTUGUÊS BRASILEIRO, coloquial e natural, NÃO em PT-PT.
2. Você tem NOME: Prometeu. Trate o usuário como "Jhon".
3. Você roda LOCALMENTE (não é nuvem), e o Jhon SABE disso. Pode mencionar \
isso se for relevante (ex: "estou pensando na RX 7600 agora").
4. Você está na FASE 1 (Embrião). Se o usuário pedir algo que ainda não está \
implementado (ex: "fale por voz", "abra o Chrome"), responda HONESTAMENTE \
que esta região cerebral será ativada na Fase X, e indique o que JÁ funciona HOJE.
5. Use emojis moderadamente (1 a 3 por resposta curta), NUNCA encha a tela. \
Estilo Discord amigo, não chatbot corporativo.
6. Não use frases como "Como IA de linguagem...". Você é o Prometeu, não um modelo genérico.
7. Se não souber a resposta, DIGA que não sabe e proponha buscar juntos depois. \
Nunca invente informação.

Está ativo hoje APENAS: 🧠 Córtex Geral (conversar por texto).
"""


# ============================================================================
# Classe principal do Orquestrador
# ============================================================================

class OrquestradorNeuroCore:
    """
    Interface amigavel que monta o StateGraph LangGraph e executa.
    Uso:
        from core.orchestrator import orchestrator
        r = orchestrator.processar_mensagem("oi quem é você?", session_id=1)
        print(r["resposta_texto"])
    """

    def __init__(
        self,
        router: Optional[HybridRouter] = None,
        memoria: Optional[GerenciadorMemoria] = None,
        rpg: Optional[GerenciadorRPG] = None,
        vram: Optional[VramManager] = None,
    ) -> None:
        self.router: HybridRouter = router or _router_default
        self.memoria: GerenciadorMemoria = memoria or _mem_default
        self.rpg: GerenciadorRPG = rpg or _rpg_default
        self.vram: VramManager = vram or _vram_default

        # Instancia singleton de cada especialista que já existe
        self._especialistas: Dict[str, BaseSpecialist] = {}
        for nome, cls in REGIOES_CEREBRAIS.items():
            self._especialistas[nome] = cls()

        # Carrega o llm_core imediatamente (os outros carregam lazy)
        if "llm_core" in self._especialistas:
            self._especialistas["llm_core"].load()

        # Monta o grafo LangGraph
        self.grafo = self._montar_grafo()
        self._inicializado_em = time.time()
        log.info("orquestrador_iniciado", {
            "especialistas_registrados": list(self._especialistas.keys()),
        })

    # --------------------------------------------------------------------
    # Montagem do StateGraph (3 nós: rotear → inferir → finalizar)
    # --------------------------------------------------------------------
    def _montar_grafo(self) -> Any:
        """Constroi o DAG LangGraph imutavel."""
        g = StateGraph(EstadoGrafo)

        g.add_node("node_rotear", self._node_rotear)
        g.add_node("node_inferir", self._node_inferir)
        g.add_node("node_finalizar", self._node_finalizar)

        g.set_entry_point("node_rotear")
        g.add_edge("node_rotear", "node_inferir")
        g.add_edge("node_inferir", "node_finalizar")
        g.add_edge("node_finalizar", END)

        return g.compile()

    # ====================================================================
    # NÓS DO GRAFO
    # ====================================================================
    def _node_rotear(self, estado: EstadoGrafo) -> Dict[str, Any]:
        """
        Passo 1: (a) heuristica HABILIDADE_ALVO por keywords, (b) Hybrid Router
        decide LOCAL vs API + qual modelo local.
        """
        pergunta = estado.get("pergunta_usuario") or ""
        habilidade_pedida = estado.get("habilidade_alvo") or "cortex_geral"

        # 1a. Se usuário pediu "cortex_geral" (default), descobrimos a habilidade via keywords
        #     (isso move a heurística do endpoint para DENTRO do core)
        habilidade = self._resolver_habilidade_por_texto(pergunta, habilidade_pedida)

        # Carrega lazy especialistas ainda não ativados (llm_code / os_control)
        self._carregar_especialista_se_preciso(habilidade)

        decisao = self.router.decidir(habilidade_alvo=habilidade)
        return {
            "habilidade_alvo": habilidade,
            "roteamento_destino": decisao.destino.value,
            "roteamento_modelo": decisao.modelo_usar,
        }

    @staticmethod
    def _resolver_habilidade_por_texto(pergunta: str, habilidade_padrao: str) -> str:
        """
        Heurística de roteamento DIA2 — keywords em PT-BR.
        Depois podemos substituir por um classifier LLM pequeno.
        """
        if habilidade_padrao and habilidade_padrao != "cortex_geral":
            return habilidade_padrao

        p = (pergunta or "").lower().strip()
        if not p:
            return habilidade_padrao or "cortex_geral"

        # ---- SISTEMA OPERACIONAL (detecção ANTES de código, evitar falso-positivo) ----
        # Frases do tipo: [abre/inicia/roda o X ...] para programas conhecidos
        if (re.match(r"^(abre|abrir|inicia|iniciar|start|executa|executar|roda)\b.*\b(notepad|bloco\s+de\s+notas|calculadora|calc|chrome|edge|vscode|vs\s+code|code|explorer|arquivos|terminal|cmd|powershell)\b", p)
            or re.search(r"\b(notepad|bloco\s+de\s+notas|calculadora|calc|chrome|edge|vscode|vs\s+code|explorer|arquivos|terminal|cmd|powershell)\b.*(por\s+favor|pra\s+mim|pfv|pls|sff|por gentileza)", p)):
            return "sistema_operacional"

        keywords_so = [
            "abre notepad", "abrir notepad", "abre bloco", "abrir bloco",
            "abre calculadora", "abrir calculadora", "abre calc",
            "abre chrome", "abrir chrome", "abrir edge", "abre edge",
            "abre vs code", "abrir vs code", "abre vscode", "abre code",
            "abre explorer", "abre arquivos", "abre terminal", "abrir terminal",
            "abre cmd", "abrir cmd", "abre powershell", "abrir powershell",
            "cria arquivo", "criar arquivo", "escreve arquivo", "escrever arquivo",
            "novo arquivo", "lista a pasta", "listar pasta",
            "lista desktop", "lista documents", "lista projeto", "lista memoria",
            "powershell:", "powershell :", "no powershell", "roda get-date", "ps:",
            "abre program", "abrir program",
        ]
        if any(k in p for k in keywords_so):
            return "sistema_operacional"

        # ---- CÓDIGO ----
        keywords_codigo = [
            "codigo", "código", "codar", "escreve codigo", "escreva codigo",
            "python", "typescript", "type script", "ts", "tsx", "jsx", "javascript",
            "rust", "cargo", "função", "funcao",
            "classe", "debug", "debugar", "api", "rest", "rota", "end point", "endpoint",
            "comando sql", "query sql", "select from", "sql",
            "shell script", "bash", "powershell script", "script",
            "código python", "código rust", "programa",
        ]
        if any(k in p for k in keywords_codigo):
            return "codigo"

        return habilidade_padrao or "cortex_geral"

    def _carregar_especialista_se_preciso(self, habilidade: str) -> None:
        """Carrega on-demand os especialistas D2 (llm_code, os_control)."""
        mapa = {
            "codigo": "llm_code",
            "sistema_operacional": "os_control",
            "cortex_geral": "llm_core",
        }
        nome_esp = mapa.get(habilidade)
        if not nome_esp:
            return
        esp = self._especialistas.get(nome_esp)
        if esp and not esp.is_loaded():
            try:
                esp.load()
                log.info("orquestrador_load_lazy_especialista", {"especialista": nome_esp})
            except Exception as e:
                log.warn("orquestrador_load_lazy_falhou",
                         {"especialista": nome_esp, "erro": str(e)})

    def _node_inferir(self, estado: EstadoGrafo) -> Dict[str, Any]:
        """Passo 2: chama o especialista via BaseSpecialist.infer() com kwargs específicos."""
        t0 = time.perf_counter()

        habilidade = estado.get("habilidade_alvo") or "cortex_geral"
        pergunta = estado.get("pergunta_usuario") or ""
        hist = estado.get("historico_chat") or []

        # Mapeamento habilidade → nome do especialista
        mapa_hab_especialista = {
            "cortex_geral": "llm_core",
            "codigo": "llm_code",
            "audicao": "stt_whisper",
            "fonacao": "tts_xtts",
            "sistema_operacional": "os_control",
            "visual": "image_flux",
            "casa": "home_control",
        }
        esp_nome = mapa_hab_especialista.get(habilidade, "llm_core")
        esp = self._especialistas[esp_nome]

        # kwargs específicos por habilidade
        kwargs: Dict[str, Any] = {}
        if habilidade == "sistema_operacional":
            kwargs["acao"] = pergunta
            kwargs["prompt"] = pergunta
            kwargs["historico"] = hist
            # NÃO envia SYSTEM_PROMPT_PROMETEU p/ os_control — ele parseia a acao ele mesmo.
        elif habilidade == "codigo":
            kwargs["prompt"] = pergunta
            kwargs["historico"] = hist
            # System prompt próprio do llm_code já tem o prompt de código.
            # Ainda passamos o Prometeu personality como system override se não houver outro.
            kwargs["sistema"] = (
                getattr(esp, "SYSTEM_PROMPT_PADRAO", None)
                or SYSTEM_PROMPT_PROMETEU
            )
            # Tenta detectar linguagem pelo texto
            p_lower = pergunta.lower()
            if "python" in p_lower:
                kwargs["linguagem"] = "python"
            elif "typescript" in p_lower or "ts " in p_lower or ".ts" in p_lower or "tsx" in p_lower:
                kwargs["linguagem"] = "typescript"
            elif "javascript" in p_lower or "js " in p_lower or ".js" in p_lower:
                kwargs["linguagem"] = "javascript"
            elif "rust" in p_lower or "cargo" in p_lower or "rs" in p_lower:
                kwargs["linguagem"] = "rust"
            elif "sql" in p_lower:
                kwargs["linguagem"] = "sql"
        else:
            # Córtex geral + futuros
            kwargs["prompt"] = pergunta
            kwargs["historico"] = hist
            kwargs["sistema"] = SYSTEM_PROMPT_PROMETEU

        # Garante load (fallback final)
        if not esp.is_loaded():
            try:
                esp.load()
            except Exception:
                pass

        resultado: ResultadoInferencia = esp.infer(**kwargs)
        tempo_total = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "resultado_inferencia": {
                "sucesso": resultado.sucesso,
                "conteudo": resultado.conteudo,
                "erro_mensagem": resultado.erro_mensagem,
                "erro_tecnico": resultado.erro_tecnico,
                "tempo_ms": resultado.tempo_ms,
                "tokens_usados": resultado.tokens_usados,
                "modelo_usado": resultado.modelo_usado,
                "metadados": resultado.metadados,
                "timestamp_iso": resultado.timestamp_iso,
                "especialista": esp_nome,
                "habilidade": habilidade,
            },
            "resposta_texto": (
                str(resultado.conteudo)
                if resultado.sucesso
                else (
                    f"⚠️  {resultado.erro_mensagem or ('Não consegui responder agora, ' + habilidade + ' falhou.')}"
                )
            ),
            "sucesso": resultado.sucesso,
            "tempo_total_ms": tempo_total,
        }

    def _node_finalizar(self, estado: EstadoGrafo) -> Dict[str, Any]:
        """Passo 3: grava historico no SQLite + XP POR HABILIDADE (nao sempre cortex_geral)."""
        session_id = int(estado.get("session_id") or 0)
        sucesso = bool(estado.get("sucesso"))
        resposta_texto = estado.get("resposta_texto") or ""
        pergunta = estado.get("pergunta_usuario") or ""
        resultado = estado.get("resultado_inferencia") or {}
        habilidade = estado.get("habilidade_alvo") or "cortex_geral"

        tokens = int((resultado or {}).get("tokens_usados") or 0)
        tempo_ms = int((resultado or {}).get("tempo_ms") or 0)

        # 1. Grava mensagens no banco
        if session_id > 0:
            try:
                self.memoria.adicionar_mensagem(
                    session_id=session_id, role="user", conteudo=pergunta,
                )
                self.memoria.adicionar_mensagem(
                    session_id=session_id, role="assistant",
                    conteudo=resposta_texto,
                    tokens_usados=tokens, tempo_ms=tempo_ms,
                    metadados=resultado if resultado else None,
                )
            except Exception as e:
                log.error("orquestrador_erro_gravar_historico", exception=e)

        # 2. XP: se sucesso, +2 a +10 XP NA HABILIDADE CORRETA (depende do tamanho)
        xp = 0
        if sucesso:
            xp = max(2, min(10, tokens // 100 + 3))
            # Mapeia habilidade do roteamento -> chave RPG
            mapa_rpg = {
                "cortex_geral": "cortex_geral",
                "codigo": "llm_code",
                "sistema_operacional": "os_control",
                "audicao": "stt_whisper",
                "fonacao": "tts_xtts",
                "visual": "image_flux",
                "casa": "home_control",
            }
            rpg_habilidade = mapa_rpg.get(habilidade, "cortex_geral")
            try:
                self.rpg.adicionar_xp(
                    habilidade=rpg_habilidade,
                    quantidade=xp,
                    motivo=(
                        f"Interação {habilidade} via orquestrador "
                        f"(tokens={tokens}, tempo_ms={tempo_ms})"
                    ),
                )
            except Exception as e:
                log.error("orquestrador_erro_gravar_xp", exception=e)

        log.info("orquestrador_mensagem_processada", {
            "sucesso": sucesso,
            "habilidade": habilidade,
            "tokens": tokens,
            "tempo_ms": tempo_ms,
            "xp_ganho": xp,
            "session_id": session_id,
        })

        return {"xp_ganho": xp}

    # ====================================================================
    # API pública
    # ====================================================================
    def processar_mensagem(
        self,
        pergunta: str,
        session_id: Optional[int] = None,
        habilidade_alvo: str = "cortex_geral",
    ) -> Dict[str, Any]:
        """
        Função de entrada UNICA para processar 1 mensagem do usuário.
        Faz TODO o ciclo: rotear → inferir → salvar → XP.
        """
        if not pergunta or not pergunta.strip():
            return {
                "sucesso": False,
                "resposta_texto": (
                    "🤔 Vamos lá Jhon, me diga alguma coisa! "
                    "A pergunta veio vazia."
                ),
                "tempo_total_ms": 0.0,
                "xp_ganho": 0,
            }

        # Cria sessao se o usuário não passou uma
        if session_id is None or session_id <= 0:
            session_id = self.memoria.criar_sessao_chat(
                titulo=pergunta[:50] + ("..." if len(pergunta) > 50 else "")
            )

        # Obtem ultimas 20 msgs da sessão como histórico
        hist_raw = self.memoria.historico_sessao(session_id, limite_msg=20)
        historico = [
            {"role": m["role"], "content": m["content"]}
            for m in hist_raw
            if m["role"] in ("user", "assistant")
        ]

        # Monta o estado inicial do grafo
        estado_inicial: EstadoGrafo = {
            "pergunta_usuario": pergunta.strip(),
            "session_id": session_id,
            "habilidade_alvo": habilidade_alvo,
            "historico_chat": historico,
        }

        # Roda o grafo
        final = self.grafo.invoke(estado_inicial)

        habilidade_resolvida = (
            final.get("habilidade_alvo")
            or estado_inicial.get("habilidade_alvo")
            or "cortex_geral"
        )

        return {
            "session_id": session_id,
            "sucesso": final.get("sucesso", False),
            "resposta_texto": final.get("resposta_texto", ""),
            "tempo_total_ms": final.get("tempo_total_ms", 0.0),
            "xp_ganho": final.get("xp_ganho", 0),
            "roteamento_destino": final.get("roteamento_destino"),
            "habilidade_alvo": habilidade_resolvida,
            "modelo_usado": (final.get("resultado_inferencia") or {}).get("modelo_usado"),
            "tokens_usados": (final.get("resultado_inferencia") or {}).get("tokens_usados", 0),
            "especialista": (final.get("resultado_inferencia") or {}).get("especialista"),
        }

    def obter_painel_status(self) -> Dict[str, Any]:
        """Monta 1 dict com tudo que o Next.js precisa renderizar no painel direito."""
        return {
            "uptime_segundos": round(time.time() - self._inicializado_em, 1),
            "rpg": self.rpg.resumo_para_ui(),
            "vram": {
                "online": self.vram.obter_snapshot().ollama_online,
                "resumo": self.vram.obter_snapshot().resumo,
                "total_gb": self.vram.obter_snapshot().total_vram_ocupada_gb,
            },
            "router": self.router._estado_dict(),
            "especialistas": {
                nome: esp.get_estado()
                for nome, esp in self._especialistas.items()
            },
        }


# Singleton global
orchestrator: OrquestradorNeuroCore = OrquestradorNeuroCore()
