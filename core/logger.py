# ============================================================================
# MODULO: logger.py
# LOGGER ESTRUTURADO JSON LINES — Prometeu / NeuroCore
#
# Todo log do sistema (debug, info, warn, error, critical) é escrito EM LINHAS
# JSON SEPARADAS em arquivos YYYY-MM-DD.jsonl.
#
# Por que JSON Lines e nao logging Python normal?
#   1. Facil de parsear em 1 ano de logs (cada linha = 1 evento completo)
#   2. Nao quebra se o processo crashar no meio de uma escrita (append-only)
#   3. Perfeito para treinamento futuro do Teacher Model (Ritual Diario)
#   4. 100% legivel por humanos (jq, VS Code format on view)
#
# Autor: NeuroCore Team
# Linguagem: Comentarios em PT-BR.
# ============================================================================

from __future__ import annotations

import collections
import json
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Literal, Optional

# ----------------------------------------------------------------------------
# RESOLUCAO DO CAMINHO (igual ao progress_rpg.py — fallback inteligente)
# ----------------------------------------------------------------------------

_PASTA_OFICIAL_LOGS: Path = Path(r"G:\memory\logs")
_PASTA_FALLBACK_LOGS: Path = Path(__file__).resolve().parent.parent / "local_memory" / "logs"


def _resolver_pasta_logs() -> Path:
    """Mesma estrategia progress_rpg: G:\优先 → fallback local."""
    try:
        if os.environ.get("FORCE_FALLBACK_MEMORY", "0") == "1":
            raise RuntimeError("Forcado fallback via env")
        _PASTA_OFICIAL_LOGS.mkdir(parents=True, exist_ok=True)
        _teste = _PASTA_OFICIAL_LOGS / ".write_test.tmp"
        with open(_teste, "w", encoding="utf-8") as f:
            f.write("ok")
        _teste.unlink()
        return _PASTA_OFICIAL_LOGS
    except Exception:
        _PASTA_FALLBACK_LOGS.mkdir(parents=True, exist_ok=True)
        return _PASTA_FALLBACK_LOGS


PASTA_LOGS: Path = _resolver_pasta_logs()

NivelLog = Literal["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]

NIVEIS_NUMERICOS: Dict[NivelLog, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


# ============================================================================
# RING BUFFER — armazena os últimos N eventos em memória RAM
# O WebSocket /ws/logs vai ler daqui sem tocar disco.
# ============================================================================

class LogRingBuffer:
    """
    Buffer circular thread-safe que guarda os últimos `maxlen` eventos de log.
    Cada evento é um dict igual ao que vai para o arquivo JSONL.
    Uso: log_buffer.snapshot() → lista dos últimos eventos (mais antigos primeiro).
    """

    def __init__(self, maxlen: int = 200) -> None:
        self._buf: Deque[Dict[str, Any]] = collections.deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, evento: Dict[str, Any]) -> None:
        """Insere 1 evento (operação O(1), thread-safe)."""
        with self._lock:
            self._buf.append(evento)

    def snapshot(self, limite: int = 200) -> List[Dict[str, Any]]:
        """Retorna cópia dos últimos `limite` eventos (mais antigos primeiro)."""
        with self._lock:
            items = list(self._buf)
        return items[-limite:] if limite < len(items) else items

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()


# Singleton global — o WebSocket importa diretamente: from core.logger import log_buffer
log_buffer: LogRingBuffer = LogRingBuffer(maxlen=200)


# ============================================================================
# CLASSE PRINCIPAL — LoggerPrometeu
# ============================================================================

class LoggerPrometeu:
    """
    Logger single-thread-safe (usa Lock interno) que escreve JSON Lines.

    Uso (em QUALQUER modulo):
        from core.logger import log
        log.info("prometeu_iniciado", {"modelo": "llama3.1", "versao": 1})
        log.error("falha_carregamento", {"erro": str(e)}, exception=e)
    """

    def __init__(self, pasta_logs_override: Optional[Path] = None) -> None:
        self._pasta: Path = pasta_logs_override if pasta_logs_override else PASTA_LOGS
        self._lock = threading.Lock()  # Garante atomicidade entre threads Python
        self._arquivo_aberto = None
        self._data_arquivo_aberto: Optional[str] = None
        # Nivel minimo para logar em arquivo (DEBUG = tudo).
        self.nivel_minimo_arquivo: int = NIVEIS_NUMERICOS["DEBUG"]
        # Nivel minimo para imprimir no stderr (terminal).
        self.nivel_minimo_console: int = NIVEIS_NUMERICOS["INFO"]

    # ------------------------------------------------------------------------
    # Gerenciamento do arquivo (rotate por data NATURALMENTE
    # Cada dia = 1 arquivo diferente, YYYY-MM-DD.jsonl
    # ------------------------------------------------------------------------
    def _obter_arquivo_hoje(self):
        """Retorna um file object para append (nao fecha o de ontem)."""
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        if (
            self._arquivo_aberto is not None
            and self._data_arquivo_aberto == data_hoje
        ):
            return self._arquivo_aberto

        # Data mudou (ou primeira chamada) — fecha o velho se tem
        if self._arquivo_aberto is not None:
            try:
                self._arquivo_aberto.close()
            except Exception:
                pass

        caminho = self._pasta / f"{data_hoje}.jsonl"
        # 'a' = append (nunca trunca)
        self._arquivo_aberto = open(caminho, "a", encoding="utf-8", buffering=1)
        self._data_arquivo_aberto = data_hoje
        return self._arquivo_aberto

    # ------------------------------------------------------------------------
    # Método genérico de log (os 5 niveis usam isso)
    # ------------------------------------------------------------------------
    def _logar(
        self,
        nivel: NivelLog,
        evento: str,
        dados: Optional[Dict[str, Any]] = None,
        exception: Optional[BaseException] = None,
    ) -> None:
        """
        Salva 1 evento de log.
        Args:
            nivel: DEBUG/INFO/WARN/ERROR/CRITICAL
            evento: ID curto humano (ex: "modelo_carregado", "erro_vram")
            dados: Dicionario flat de contexto (ex: {"modelo": "llama3", "vram_mb": 5400})
            exception: Se passou uma excecao, loga stacktrace automaticamente
        """
        nivel_num = NIVEIS_NUMERICOS[nivel]

        # 1. Monta o payload do evento (um dict = 1 linha JSON)
        payload: Dict[str, Any] = {
            "ts": datetime.now().astimezone().isoformat(timespec="milliseconds"),
            "nivel": nivel,
            "evento": evento,
        }
        if dados:
            payload["dados"] = dados
        if exception is not None:
            payload["excecao"] = {
                "tipo": type(exception).__name__,
                "mensagem": str(exception),
                "traceback": traceback.format_exc(),
            }

        # 2. Escreve no console (stderr) se passar do nivel
        if nivel_num >= self.nivel_minimo_console:
            try:
                print(
                    f"[{payload['ts'][11:19]}] {nivel:<8} {evento:<28} | "
                    f"{json.dumps(dados or {}, ensure_ascii=False)[:140]}",
                    file=sys.stderr,
                    flush=True,
                )
            except Exception:
                pass  # Printar falha de log nao pode quebrar o app

        # 3. Alimenta o ring buffer em memória (para WebSocket /ws/logs)
        log_buffer.add(payload)

        # 4. Escreve no arquivo JSON Lines (atomicamente com Lock)
        if nivel_num >= self.nivel_minimo_arquivo:
            with self._lock:
                try:
                    arquivo = self._obter_arquivo_hoje()
                    arquivo.write(json.dumps(payload, ensure_ascii=False) + "\n")
                    arquivo.flush()
                    os.fsync(arquivo.fileno())
                except Exception:
                    # Falha de escrita em log NUNCA pode quebrar a aplicacao
                    try:
                        print(
                            f"[LOGGER FALHOU] impossivel gravar log em {self._pasta}",
                            file=sys.stderr,
                        )
                    except Exception:
                        pass

    # ------------------------------------------------------------------------
    # Métodos públicos (5 níveis)
    # ------------------------------------------------------------------------
    def debug(self, evento: str, dados: Optional[Dict[str, Any]] = None) -> None:
        """Detalhes de baixo nível (ex: valor de variavel interna)."""
        self._logar("DEBUG", evento, dados)

    def info(self, evento: str, dados: Optional[Dict[str, Any]] = None) -> None:
        """Eventos normais de operacao (ex: modelo carregado)."""
        self._logar("INFO", evento, dados)

    def warn(self, evento: str, dados: Optional[Dict[str, Any]] = None,
             exception: Optional[BaseException] = None) -> None:
        """Situacoes preocupantes mas o programa continua (ex: VRAM 85%)."""
        self._logar("WARN", evento, dados, exception)

    def error(self, evento: str, dados: Optional[Dict[str, Any]] = None,
              exception: Optional[BaseException] = None) -> None:
        """Erros que afetam 1 operacao mas o app nao cai (ex: 1 chamada falhou)."""
        self._logar("ERROR", evento, dados, exception)

    def critical(self, evento: str, dados: Optional[Dict[str, Any]] = None,
                 exception: Optional[BaseException] = None) -> None:
        """Erros fatais — o processo vai morrer (ex: impossivel carregar cérebro)."""
        self._logar("CRITICAL", evento, dados, exception)

    # ------------------------------------------------------------------------
    # Utils public
    # ------------------------------------------------------------------------
    def obter_caminho_hoje(self) -> Path:
        """Retorna qual o arquivo de log de hoje (para UI exibir)."""
        data = datetime.now().strftime("%Y-%m-%d")
        return self._pasta / f"{data}.jsonl"

    def __del__(self) -> None:
        """Fecha arquivo aberto no garbage collector."""
        if self._arquivo_aberto is not None:
            try:
                self._arquivo_aberto.close()
            except Exception:
                pass


# ============================================================================
# SINGLETON GLOBAL — qualquer módulo importa: from core.logger import log
# ============================================================================
log: LoggerPrometeu = LoggerPrometeu()
