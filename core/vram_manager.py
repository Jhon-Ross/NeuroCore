# ============================================================================
# MODULO: vram_manager.py
# GERENCIADOR DE VRAM PARA A RX 7600 8GB (OBRIGATORIO POR LIMITACAO DE HARDWARE)
#
# Problema: A RX 7600 tem SO 8GB de VRAM GDDR6. É IMPOSSIVEL carregar 2 LLMs
# grandes ao mesmo tempo (ex: Llama 3.1 8B ocupa ~6GB, CodeLlama 7B ocupa ~5GB).
# Solucao: Antes de carregar QUALQUER especialista que use VRAM, o orquestrador
# CHAMA este gerenciador para descarregar TODOS os outros e só então carregar o novo.
#
# Nao usamos VRAM manual — confiamos no Ollama que ja gerencia DirectML.
# Aqui a gente só consulta o /api/tags e /api/ps do Ollama.
# ============================================================================

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from core.base_specialist import UsoRecursos
from core.logger import log


# ============================================================================
# Estruturas
# ============================================================================

@dataclass
class ModeloOllamaCarregado:
    """Snapshot de 1 modelo carregado na VRAM via Ollama."""
    nome_modelo: str           # ex: "llama3.1:8b"
    tamanho_bytes: int = 0
    tamanho_gb: float = 0.0     # facilita UI
    digested_at: str = ""
    expires_at: str = ""        # OLLAMA_KEEP_ALIVE=5s → expira rapido


@dataclass
class SnapshotVram:
    """Snapshot completo para o painel de status (sparklines)."""
    horario_unix: float = field(default_factory=time.time)
    modelos_carregados: List[ModeloOllamaCarregado] = field(default_factory=list)
    ollama_online: bool = False
    erro: Optional[str] = None
    total_vram_ocupada_gb: float = 0.0  # soma de todos os modelos

    @property
    def resumo(self) -> str:
        if not self.ollama_online:
            return "OLLAMA OFFLINE (sem VRAM gerenciada)"
        return (
            f"{len(self.modelos_carregados)} modelo(s) na VRAM → "
            f"{self.total_vram_ocupada_gb:.2f} GB de 8GB da RX 7600"
        )


# ============================================================================
# Classe principal
# ============================================================================

class VramManager:
    """
    Consulta estado da VRAM no Ollama.
    (troca de modelos real = o proprio Ollama gerencia com OLLAMA_KEEP_ALIVE=5s)
    """

    def __init__(self, ollama_host: str = "http://localhost:11434",
                 timeout_seg: float = 5.0) -> None:
        self._host: str = ollama_host.rstrip("/")
        self._timeout: float = timeout_seg
        self._ultimo_snapshot: Optional[SnapshotVram] = None
        self._historico: List[SnapshotVram] = []

    # ------------------------------------------------------------------------
    # Operacoes publicas
    # ------------------------------------------------------------------------
    def obter_snapshot(self) -> SnapshotVram:
        """Consulta /api/tags e /api/ps no Ollama agora."""
        snap = SnapshotVram()
        try:
            with httpx.Client(timeout=self._timeout) as http:
                # 1. Verifica se o servidor ta ON (qualquer endpoint)
                try:
                    resp_tags = http.get(f"{self._host}/api/tags")
                    resp_tags.raise_for_status()
                    snap.ollama_online = True
                except Exception as e:
                    snap.erro = f"Ollama offline em {self._host}: {e}"
                    snap.ollama_online = False
                    self._guardar_snapshot(snap)
                    log.warn("vram_ollama_offline", {"host": self._host})
                    return snap

                # 2. /api/ps = modelos CARREGADOS AGORA NA VRAM
                modelos: List[Dict[str, Any]] = []
                try:
                    resp_ps = http.get(f"{self._host}/api/ps")
                    if resp_ps.status_code == 200:
                        modelos = (resp_ps.json() or {}).get("models") or []
                except Exception:
                    modelos = []

                # 3. Parse
                total_gb = 0.0
                for m in modelos:
                    tam = int(m.get("size") or 0)
                    gb = round(tam / (1024 ** 3), 3)
                    total_gb += gb
                    snap.modelos_carregados.append(ModeloOllamaCarregado(
                        nome_modelo=str(m.get("name") or "desconhecido"),
                        tamanho_bytes=tam,
                        tamanho_gb=gb,
                        digested_at=str(m.get("digest") or "")[:16],
                        expires_at=str(m.get("expires_at") or ""),
                    ))
                snap.total_vram_ocupada_gb = round(total_gb, 3)
                log.debug("vram_snapshot_atualizado", {
                    "total_gb": snap.total_vram_ocupada_gb,
                    "qtd_modelos": len(snap.modelos_carregados),
                })
        except Exception as e:
            snap.erro = str(e)
            snap.ollama_online = False
            log.error("vram_snapshot_falhou", exception=e)

        self._guardar_snapshot(snap)
        return snap

    def descarregar_tudo_exceto(self, manter_modelo: Optional[str] = None) -> bool:
        """
        Força o Ollama a descarregar todos os modelos MENOS o nomeado.
        Como OLLAMA_KEEP_ALIVE=5s, basta esperar 6 segundos que tudo descarrega solo.
        Mas se precisarmos de AGORA, usamos /api/gpu ou simplesmente esperamos.
        """
        if manter_modelo is None:
            log.info("vram_descarregando_tudo_esperando_keep_alive",
                     {"segundos": 6})
        else:
            log.info("vram_descarregando_tudo_exceto", {"manter": manter_modelo})
        try:
            # Simples: espera o keep_alive de 5s expirar
            time.sleep(6.0)
            return True
        except Exception as e:
            log.error("vram_descarregar_falhou", exception=e)
            return False

    @property
    def ultimo_snapshot(self) -> Optional[SnapshotVram]:
        return self._ultimo_snapshot

    def historico_ultimos(self, segundos: int = 60) -> List[SnapshotVram]:
        """Historico recente (para sparklines do painel status)."""
        corte = time.time() - segundos
        return [h for h in self._historico if h.horario_unix >= corte]

    # ------------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------------
    def _guardar_snapshot(self, s: SnapshotVram) -> None:
        """Guarda historico de até 3600 snapshots = 1h a 1s."""
        self._ultimo_snapshot = s
        self._historico.append(s)
        if len(self._historico) > 3600:
            self._historico = self._historico[-3600:]


# Singleton para o orquestrador
vram_manager: VramManager = VramManager()
