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
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# fallback sandbox TRAE (forca local_memory sem acessar G:)
import os as _os
_os.environ.setdefault("FORCE_FALLBACK_MEMORY", "1")

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


class StatusResponse(BaseModel):
    timestamp_unix: float
    timestamp_iso: str
    uptime_segundos: float
    rpg: Dict[str, Any]
    vram: Dict[str, Any]
    router: Dict[str, Any]
    especialistas: Dict[str, Any]
    servidor_api: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    )


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest) -> ChatResponse:
    """
    Acceptance Criteria DIA 2 #1: retorna 200 com llama3:latest sem crash.
    Invoca o orquestrador.processar_mensagem() com a heuristica de
    habilidade_alvo baseada em keywords (se o usuário passou 'auto').
    """
    msg = req.mensagem.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    habilidade = _resolver_habilidade(req.habilidade_alvo, msg)

    # Executa em thread separada pq orquestrador.sync invoca Ollama bloqueante.
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(
            None,  # default ThreadPoolExecutor
            lambda: orchestrator.processar_mensagem(
                pergunta=msg,
                session_id=req.session_id,
                habilidade_alvo=habilidade,
            ),
        )
    except Exception as e:
        log.error("api_chat_erro", {"mensagem": msg[:80], "habilidade": habilidade}, exception=e)
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
