# ============================================================================
# MODULO: api.py
# FASTAPI CORE :8000 — PONTE ENTRE NEXT.JS (UI) E O PROMETEU (ORQUESTRADOR)
#
# Prioridade ABSOLUTA do Dia 2. Tudo que o navegador (e futuramente
# B2B, Telegram, WhatsApp) vai usar como "porta de entrada" sai daqui.
#
# 3 endpoints OBRIGATORIOS da maratona:
#   POST   /api/chat        · recebe {mensagem, session_id?} → processar_mensagem()
#   GET    /api/status      · obter_painel_status() sem inferencia
#   WS     /ws/sparklines   · streaming a cada 1s de sinais vitais (CPU/VRAM/XP)
#
# Seguranca:
#   CORS apenas para http://localhost:3000 (frontend do Next).
#   Nenhum endpoint recebe credenciais externas, tudo LOCAL.
# ============================================================================

from __future__ import annotations

import asyncio
import json
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# fallback sandbox TRAE (forca local_memory sem acessar G:)
import os as _os
_os.environ.setdefault("FORCE_FALLBACK_MEMORY", "1")

# ---------------------------------------------------------------------------
# CARREGADOR MANUAL DO .env (NÃO depende de python-dotenv pip)
# Garante que ANTES de instanciar o HybridRouter / Orchestrator (singletons)
# as variáveis GEMINI_API_KEY, ANTHROPIC_API_KEY, PROMETEU_TETO_MENSAL_REAIS
# estejam disponíveis em os.environ. Se a variável já estiver no shell,
# NÃO sobreescreve (setdefault).
# ---------------------------------------------------------------------------
_CAMINHO_ENV = Path(__file__).resolve().parent.parent / ".env"
if _CAMINHO_ENV.exists():
    with open(_CAMINHO_ENV, "r", encoding="utf-8") as _f_env:
        for _linha in _f_env:
            _linha = _linha.strip()
            if not _linha or _linha.startswith("#") or "=" not in _linha:
                continue
            _chave, _, _valor = _linha.partition("=")
            _chave = _chave.strip()
            _valor = _valor.strip().strip("\"'")
            if _chave and _valor:
                _os.environ.setdefault(_chave, _valor)

from core.logger import log
from core.orchestrator import orchestrator

# ---------------------------------------------------------------------------
# Lifespan: inicializa / destroi recursos com a API
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    log.info("api_fastapi_startup", {"port": 8000, "cors": _CORS_ORIGINS})
    try:
        st = orchestrator.obter_painel_status()
        log.info("api_orquestrador_inicializado_ok", {
            "uptime": st.get("uptime_segundos"),
            "nivel_global": (st.get("rpg") or {}).get("nivel_global"),
        })
    except Exception as e:
        log.error("api_orquestrador_inicializado_erro", exception=e)
    yield
    # SHUTDOWN
    log.info("api_fastapi_shutdown")


app = FastAPI(
    title="NeuroCore Prometeu Backend API",
    version="0.1.0-dia2",
    description="Cérebro local do Prometeu — orquestrador LangGraph + 7 regiões.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS: wildcard "*" no localhost (ambiente 100% local, sem rede externa).
# Motivo: Tauri v2 WebView2 tem origens dinâmicas (tauri://localhost,
# https://tauri.localhost, null, file:// etc.) que mudam por build. Com "*",
# Next.js (http://localhost:3000), Navegador Preview, e Desktop Tauri
# todos funcionam sem bloqueio de CORS no fetch() do navegador.
# ---------------------------------------------------------------------------
_CORS_ORIGINS: List[str] = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,  # false quando allow_origins="*" (padrão CORS spec)
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas de request / response Pydantic (tipo forte)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=8000, description="Mensagem do usuário")
    session_id: Optional[int] = Field(default=None, description="Sessão já existente (SQLite)")
    habilidade_alvo: str = Field(
        default="auto",
        description="Força habilidade: 'auto', 'cortex_geral', 'codigo', 'sistema_operacional'",
    )
    provider: str = Field(
        default="auto",
        description=(
            "Seleção de provider de inferência: "
            "'auto' = Prometeu decide por heurística (padrão recomendado), "
            "'local' = Ollama RX 7600 local SEMPRE (R$0.00), "
            "'openrouter' = OpenRouter agregador, "
            "'anthropic' = Anthropic Claude 3.5 direto, "
            "'gemini' = Google Gemini 3.5 Flash-Lite direto (camada gratuita)"
        ),
    )


class ChatResponse(BaseModel):
    session_id: int
    sucesso: bool
    resposta_texto: str
    tempo_total_ms: float
    xp_ganho: int
    modelo_usado: Optional[str] = None
    tokens_usados: int = 0
    habilidade_alvo: Optional[str] = None
    roteamento_destino: Optional[Any] = None
    # --- NOVOS CAMPOS PROVIDER ---
    roteamento_provedor: Optional[str] = None
    roteamento_motivo: Optional[str] = None
    custo_estimado_reais: float = 0.0


class StatusResponse(BaseModel):
    timestamp_unix: float
    timestamp_iso: str
    uptime_segundos: float
    rpg: Dict[str, Any]
    vram: Dict[str, Any]
    router: Dict[str, Any]
    especialistas: Dict[str, Any]
    servidor_api: Dict[str, Any]
    # --- NOVO CAMPO: Lista de providers p/ UI renderizar dropdown ---
    providers_disponiveis: List[Dict[str, Any]]


class CodeRunRequest(BaseModel):
    codigo: str = Field(..., description="Código-fonte a ser executado")
    linguagem: str = Field(default="python", description="Linguagem: python, powershell, javascript, bash")
    timeout_segundos: int = Field(default=15, description="Timeout em segundos (máx 60)")


class CodeRunResponse(BaseModel):
    sucesso: bool
    stdout: str
    stderr: str
    codigo_retorno: int
    tempo_ms: float
    linguagem: str
    xp_ganho: int


# --- HISTÓRICO DE SESSÕES ---

class SessaoItem(BaseModel):
    id: int
    titulo: str
    criado_em: str
    atualizado_em: str
    total_mensagens: int = 0

class ListaSessoesResponse(BaseModel):
    sessoes: List[SessaoItem]
    total: int


class MensagemItem(BaseModel):
    id: int
    role: str          # "user" | "assistant"
    content: str
    timestamp_iso: str
    tokens_usados: int = 0
    tempo_ms: int = 0

class HistoricoSessaoResponse(BaseModel):
    session_id: int
    titulo: str
    mensagens: List[MensagemItem]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Valores válidos para `provider` no request (evita injection)
_PROVIDERS_VALIDOS: frozenset[str] = frozenset({
    "auto", "local", "openrouter", "anthropic", "gemini",
})

# Label e ÍCONE para cada provider (para UI renderizar dropdown)
_PROVIDERS_METADADOS: List[Dict[str, Any]] = [
    {
        "valor": "auto",
        "label": "🔮 Automático (Prometeu decide)",
        "descricao": "O próprio Prometeu escolhe: Ollama LOCAL para conversa casual, "
                     "Anthropic para código avançado e arquitetura.",
        "custo_nominal_brl": 0.0,  # pode ou não gastar
        "requer_chave": False,     # funciona SEMPRE (cai local por padrão)
    },
    {
        "valor": "local",
        "label": "🧠 Ollama RX 7600 (Local · Sempre recomendado)",
        "descricao": "100% local na sua GPU AMD RX 7600 8GB. R$0.00 por resposta. "
                     "Privacidade máxima. Nenhuma informação sai do seu PC.",
        "custo_nominal_brl": 0.0,
        "requer_chave": False,
    },
    {
        "valor": "anthropic",
        "label": "✨ Anthropic Claude Direto",
        "descricao": "Melhor raciocínio técnico/arquitetura hoje. Custo ~R$0.03~R$0.30 "
                     "por resposta (depende do tamanho).",
        "custo_nominal_brl": 0.03,
        "requer_chave": True,
        "env_var": "ANTHROPIC_API_KEY",
    },
    {
        "valor": "openrouter",
        "label": "🌐 OpenRouter Agregador",
        "descricao": "1 chave = GPT-4o, Claude, Gemini, Llama Cloud +100 outros. "
                     "Bom para testar vários modelos rapidamente.",
        "custo_nominal_brl": 0.03,
        "requer_chave": True,
        "env_var": "OPENROUTER_API_KEY",
    },
    {
        "valor": "gemini",
        "label": "🪄 Google Gemini Direto",
        "descricao": "Bom balanço custo × qualidade para tarefas gerais.",
        "custo_nominal_brl": 0.01,
        "requer_chave": True,
        "env_var": "GEMINI_API_KEY",
    },
]


def _resolver_habilidade(habilidade_alvo: str, _mensagem: str) -> str:
    """
    NOTA DIA 2: a heurística de keywords AGORA VIVE NO ORQUESTRADOR
    (core.orchestrator._resolver_habilidade_por_texto), não mais aqui.
    Mantemos esta função somente p/ compatibilidade: se o usuário pediu
    'auto' ou vazio, deixamos o orquestrador decidir (passamos 'cortex_geral' = default lá).
    Qualquer outro valor (ex: habilidade_alvo='codigo' explicitamente do UI) passa reto.
    """
    if not habilidade_alvo or habilidade_alvo in ("auto", ""):
        return "cortex_geral"   # default do orquestrador = vai rodar a heurística keywords
    return habilidade_alvo


def _normalizar_provider(provider_input: str | None) -> str:
    """Garante que o `provider` recebido do request é um valor válido.
    Nunca retorna string arbitrária para o orquestrador.
    """
    if not provider_input:
        return "auto"
    p = provider_input.strip().lower()
    return p if p in _PROVIDERS_VALIDOS else "auto"


def _montar_providers_disponiveis() -> List[Dict[str, Any]]:
    """Retorna a lista completa para a UI renderizar, com o campo 'disponivel'
    calculado (True se tem chave configurada OU não precisa de chave).
    """
    from core.hybrid_router import hybrid_router
    mapa_tem_chave: Dict[str, bool] = {
        nome: tem for nome, tem in hybrid_router.providers_disponiveis()
    }
    teto_atual_reais: float = float(_os.environ.get("PROMETEU_TETO_MENSAL_REAIS", "0.0") or 0.0)
    teto_bloqueado: bool = teto_atual_reais <= 0.0
    resultado: List[Dict[str, Any]] = []
    for meta in _PROVIDERS_METADADOS:
        valor = meta["valor"]
        if not meta["requer_chave"]:
            disponivel = True
        else:
            tem_chave = bool(mapa_tem_chave.get(valor, False))
            disponivel = tem_chave and not teto_bloqueado
        item = {**meta, "disponivel": disponivel}
        if meta["requer_chave"] and not disponivel:
            tem_chave = bool(mapa_tem_chave.get(valor, False))
            motivos: List[str] = []
            if not tem_chave:
                motivos.append(f"Chave {meta['env_var']} NÃO configurada no arquivo .env")
            else:
                motivos.append(f"Chave {meta['env_var']} OK")
            if teto_bloqueado:
                motivos.append(
                    "TETO MENSAL BLOQUEADO em R$0.00 "
                    "(mude PROMETEU_TETO_MENSAL_REAIS no .env para ativar APIs externas)"
                )
            else:
                motivos.append(f"Teto mensal atual: R${teto_atual_reais:.2f}")
            item["motivo_indisponivel"] = " · ".join(motivos)
        resultado.append(item)
    return resultado


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/")
async def root() -> Dict[str, Any]:
    """Health check leve."""
    return {
        "ok": True,
        "servico": "NeuroCore Prometeu Backend API",
        "versao": "0.1.0-dia2",
        "docs_swagger": "/docs",
        "links": ["/api/status", "/api/chat", "/ws/sparklines"],
    }


@app.get("/api/status", response_model=StatusResponse)
async def api_status() -> StatusResponse:
    """
    Tudo que o Next.js precisa pra renderizar o painel direito RPG
    e os sparklines SEM rodar inferência (rápido ~30ms).
    """
    try:
        st = orchestrator.obter_painel_status()
    except Exception as e:
        log.error("api_status_erro", exception=e)
        raise HTTPException(status_code=500, detail="Orquestrador falhou em obter_painel_status")

    now = time.time()
    return StatusResponse(
        timestamp_unix=now,
        timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
        uptime_segundos=float(st.get("uptime_segundos") or 0),
        rpg=st.get("rpg") or {},
        vram=st.get("vram") or {},
        router=st.get("router") or {},
        especialistas=st.get("especialistas") or {},
        servidor_api={
            "cors_origins": _CORS_ORIGINS,
            "porta": 8000,
        },
        providers_disponiveis=_montar_providers_disponiveis(),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest) -> ChatResponse:
    """
    Acceptance Criteria DIA 2 #1: retorna 200 com llama3:latest sem crash.
    Invoca o orquestrador.processar_mensagem() com a heuristica de
    habilidade_alvo baseada em keywords (se o usuário passou 'auto').

    Suporta AGORA seleção de PROVIDER via campo req.provider:
      - "auto" (padrão) → Prometeu decide por heurística
      - "local" → Ollama RX 7600 SEMPRE
      - "anthropic"/"openrouter"/"gemini" → força provider específico
    """
    msg = req.mensagem.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    habilidade = _resolver_habilidade(req.habilidade_alvo, msg)
    provider = _normalizar_provider(req.provider)

    # Executa em thread separada pq orquestrador.sync invoca Ollama bloqueante.
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(
            None,  # default ThreadPoolExecutor
            lambda: orchestrator.processar_mensagem(
                pergunta=msg,
                session_id=req.session_id,
                habilidade_alvo=habilidade,
                override_provider=provider,
                heuristica_escolha_automatica=(provider == "auto"),
            ),
        )
    except Exception as e:
        log.error("api_chat_erro", {"mensagem": msg[:80], "habilidade": habilidade, "provider": provider}, exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao processar mensagem (veja logs)")

    return ChatResponse(
        session_id=int(resultado.get("session_id") or 0),
        sucesso=bool(resultado.get("sucesso")),
        resposta_texto=str(resultado.get("resposta_texto") or ""),
        tempo_total_ms=float(resultado.get("tempo_total_ms") or 0.0),
        xp_ganho=int(resultado.get("xp_ganho") or 0),
        modelo_usado=resultado.get("modelo_usado"),
        tokens_usados=int(resultado.get("tokens_usados") or 0),
        habilidade_alvo=resultado.get("habilidade_alvo") or habilidade,
        roteamento_destino=resultado.get("roteamento_destino"),
        roteamento_provedor=resultado.get("roteamento_provedor"),
        roteamento_motivo=resultado.get("roteamento_motivo"),
        custo_estimado_reais=float(resultado.get("custo_estimado_reais") or 0.0),
    )


@app.post("/api/code/run", response_model=CodeRunResponse)
async def api_code_run(req: CodeRunRequest) -> CodeRunResponse:
    """Executa um bloco de código de forma segura na sandbox local (Code Runner)."""
    cod = req.codigo.strip()
    if not cod:
        raise HTTPException(status_code=400, detail="Código não fornecido.")

    timeout = min(max(req.timeout_segundos, 1), 60)

    from core.code_runner import executar_codigo

    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(
            None,
            lambda: executar_codigo(
                codigo=cod,
                linguagem=req.linguagem,
                timeout_segundos=timeout,
                conceder_xp=True,
            ),
        )
    except Exception as e:
        log.error("api_code_run_erro", {"erro": str(e)}, exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao executar código")

    return CodeRunResponse(
        sucesso=resultado["sucesso"],
        stdout=resultado["stdout"],
        stderr=resultado["stderr"],
        codigo_retorno=resultado["codigo_retorno"],
        tempo_ms=resultado["tempo_ms"],
        linguagem=resultado["linguagem"],
        xp_ganho=resultado["xp_ganho"],
    )



# ---------------------------------------------------------------------------
# HISTÓRICO DE CONVERSAS: GET /api/chat/sessions
# ---------------------------------------------------------------------------

@app.get("/api/chat/sessions", response_model=ListaSessoesResponse)
async def api_listar_sessoes(limite: int = 50) -> ListaSessoesResponse:
    """
    Lista as últimas N sessões de chat salvas no SQLite.
    Retorna id, título, data de criação/atualização e total de mensagens.
    """
    try:
        sessoes_raw = orchestrator.memoria.listar_sessoes(limite=min(limite, 100))
    except Exception as e:
        log.error("api_listar_sessoes_erro", {"erro": str(e)}, exception=e)
        raise HTTPException(status_code=500, detail="Erro ao listar sessões do SQLite.")

    # Conta mensagens de cada sessão (em thread separada para não bloquear)
    loop = asyncio.get_event_loop()

    def _contar_msgs(session_id: int) -> int:
        try:
            return len(orchestrator.memoria.historico_sessao(session_id, limite_msg=1000))
        except Exception:
            return 0

    itens: List[SessaoItem] = []
    for s in sessoes_raw:
        total_msgs = await loop.run_in_executor(None, _contar_msgs, s["id"])
        itens.append(SessaoItem(
            id=s["id"],
            titulo=s["titulo"] or "Conversa sem título",
            criado_em=s["criado_em"] or "",
            atualizado_em=s["atualizado_em"] or "",
            total_mensagens=total_msgs,
        ))

    return ListaSessoesResponse(sessoes=itens, total=len(itens))


@app.get("/api/chat/sessions/{session_id}/messages", response_model=HistoricoSessaoResponse)
async def api_historico_sessao(session_id: int, limite: int = 100) -> HistoricoSessaoResponse:
    """
    Retorna as mensagens de uma sessão específica do SQLite.
    Permite ao frontend carregar qualquer conversa passada e exibir no chat.
    """
    try:
        sessoes = orchestrator.memoria.listar_sessoes(limite=1000)
        sessao = next((s for s in sessoes if s["id"] == session_id), None)
        if sessao is None:
            raise HTTPException(status_code=404, detail=f"Sessão #{session_id} não encontrada.")

        loop = asyncio.get_event_loop()
        msgs_raw = await loop.run_in_executor(
            None,
            lambda: orchestrator.memoria.historico_sessao(session_id, limite_msg=min(limite, 500)),
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error("api_historico_sessao_erro", {"session_id": session_id, "erro": str(e)}, exception=e)
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico da sessão.")

    mensagens = [
        MensagemItem(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            timestamp_iso=m.get("timestamp_iso") or "",
            tokens_usados=int(m.get("tokens_usados") or 0),
            tempo_ms=int(m.get("tempo_ms") or 0),
        )
        for m in msgs_raw
        if m["role"] in ("user", "assistant")
    ]

    return HistoricoSessaoResponse(
        session_id=session_id,
        titulo=sessao["titulo"] or "Conversa sem título",
        mensagens=mensagens,
        total=len(mensagens),
    )


# ---------------------------------------------------------------------------
# WEBSOCKET: /ws/sparklines · streaming 1s de sinais vitais
# ---------------------------------------------------------------------------

@app.websocket("/ws/sparklines")
async def ws_sparklines(websocket: WebSocket):
    """
    Envia a cada ~1 segundo:
      { t, rpg { xp_total, nivel_global, habilidades[] }, vram { online, total_gb }, cpu_pct, memoria_rss_mb }
    """
    await websocket.accept()
    log.info("ws_sparklines_conectado")

    # CPU sampling precisa de 2 leituras
    try:
        import psutil
    except Exception:
        psutil = None

    try:
        while True:
            t0 = time.perf_counter()
            try:
                st = orchestrator.obter_painel_status()
                payload: Dict[str, Any] = {
                    "timestamp_unix": time.time(),
                    "uptime_segundos": st.get("uptime_segundos"),
                    "rpg": {
                        "nivel_global": (st.get("rpg") or {}).get("nivel_global"),
                        "xp_total": (st.get("rpg") or {}).get("xp_total"),
                        "habilidades": (st.get("rpg") or {}).get("habilidades", []),
                        "feitos": (st.get("rpg") or {}).get("feitos", []),
                    },
                    "vram": st.get("vram") or {},
                    "router": st.get("router") or {},
                }
                if psutil is not None:
                    try:
                        payload["cpu_pct"] = psutil.cpu_percent(interval=None)
                        payload["ram_uso_gb"] = round(
                            psutil.virtual_memory().used / (1024 ** 3), 2
                        )
                    except Exception:
                        pass
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))
            except WebSocketDisconnect:
                raise
            except Exception as e:
                log.error("ws_sparklines_erro_envio", exception=e)
                try:
                    await websocket.send_text(json.dumps({"erro": "envio_falhou", "t": time.time()}, ensure_ascii=False))
                except Exception:
                    break

            # Garante ~1s entre envios (não depender de sleep 100%)
            delta = time.perf_counter() - t0
            await asyncio.sleep(max(0.1, 1.0 - delta))
    except WebSocketDisconnect:
        log.info("ws_sparklines_desconectado")
    except Exception as e:
        log.error("ws_sparklines_critico", exception=e)


# ---------------------------------------------------------------------------
# CLI bootstrap: python core/api.py roda uvicorn na :8000
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "core.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,        # desativado no ambiente real (usar reload só dev IDE externa)
        log_level="info",
    )
