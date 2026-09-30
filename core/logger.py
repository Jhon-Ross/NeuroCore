# ============================================================================
# MODULO: logger.py
# LOGGER ESTRUTURADO JSON LINES — Prometeu / NeuroCore (v2 - Event-Driven)
#
# Esta versão refatora o sistema para um padrão de publicação/assinatura (Pub/Sub).
# O objetivo é que qualquer módulo que gere um evento log (Memory, Routing, etc.)
# possa notificar todos os componentes interessados (UI WebSocket, Debugger, Arquivo)
# através de um único ponto central.
# ============================================================================

from __future__ import annotations

import collections
import json
import os
import sys
import asyncio # Importando asyncio para operações assíncronas
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Literal, Optional, Callable

# ============================================================================
# 1. CONFIGURAÇÃO DE ARQUIVOS E ESTADO GLOBAL (SINGLETION)
# ============================================================================

_PASTA_OFICIAL_LOGS: Path = Path(r"G:\memory\logs")
_PASTA_FALLBACK_LOGS: Path = Path(__file__).resolve().parent.parent / "local_memory" / "logs"

# Estado Singleton do Logger
logger_instance: Optional[Logger] = None

class ListenerCallback:
    """Estrutura para guardar o callback de um listener."""
    def __init__(self, callback: Callable[[Dict], Any]):
        self.callback = callback

class Logger:
    """Gerenciador central de logs do sistema (Publisher)."""

    # Estruturas de dados de estado
    _subscribers: List[ListenerCallback] = [] # Lista de callbacks registrados
    log_buffer_history: Deque[Dict] = collections.deque(maxlen=200)

    def __init__(self):
        print("[LOGGER INIT]: Inicializando o logger central...")
        self._path_logs = self._resolver_pasta_logs()
        self._lock = threading.Lock()
        # Thread worker dedicada para rodar as coroutines de escrita/pub de forma FIFO
        # (assim os métodos info/warn/error ficam síncronos fire-and-forget e não
        # precisam ser awaited — compatibilidade com 100% dos módulos já existentes
        # que chamam log.info(...) no top-level / __init__ sem async def).
        self._shutdown_flag = False
        self._queue_worker: Optional[threading.Thread] = None
        self._worker_loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: "asyncio.Queue[Dict]" = None  # type: ignore[assignment]
        self._ensure_worker_thread_started()

    # ------------------------------------------------------------
    # Worker thread interna dedicada para rodar async coroutines
    # ------------------------------------------------------------
    def _ensure_worker_thread_started(self) -> None:
        if self._queue_worker is not None and self._queue_worker.is_alive():
            return

        started = threading.Event()

        def _rodar_loop_em_thread_dedicada():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._worker_loop = loop
                self._queue = asyncio.Queue(maxsize=10000)

                async def _drain_queue():
                    while not self._shutdown_flag:
                        try:
                            evento = await asyncio.wait_for(self._queue.get(), timeout=0.25)
                        except TimeoutError:
                            continue
                        try:
                            # Publica + persiste (operações IO assíncronas)
                            await self._publish_event(evento)
                        except Exception as e:
                            print(f"[LOGGER WORKER ERROR]: Falha publicando evento: {e}", file=sys.stderr)
                            traceback.print_exc(file=sys.stderr)
                        finally:
                            try:
                                self._queue.task_done()
                            except Exception:
                                pass

                started.set()
                try:
                    loop.run_until_complete(_drain_queue())
                finally:
                    # Flush final: esvaziar o que sobrou na fila
                    try:
                        pendentes = []
                        while not self._queue.empty():
                            pendentes.append(self._queue.get_nowait())
                        if pendentes:
                            loop.run_until_complete(asyncio.gather(
                                *[self._publish_event(ev) for ev in pendentes],
                                return_exceptions=True,
                            ))
                    except Exception:
                        pass
                    try:
                        loop.close()
                    except Exception:
                        pass
            except Exception as e:
                print(f"[LOGGER WORKER CRASH]: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                started.set()  # evita deadlock no started.wait() abaixo

        t = threading.Thread(
            target=_rodar_loop_em_thread_dedicada,
            name="NeuroCoreLoggerWorker",
            daemon=True,
        )
        self._queue_worker = t
        t.start()
        started.wait(timeout=5.0)

    @staticmethod
    def _get_instance() -> Logger:
        """Garante que apenas uma instância do Logger exista (Singleton)."""
        global logger_instance
        if logger_instance is None:
            logger_instance = Logger()
        return logger_instance

    @staticmethod
    async def get_instance() -> Logger:
        """Ponto de acesso assíncrono ao singleton."""
        if logger_instance is None:
            # Em um ambiente real, esta inicialização deveria ser feita no app startup.
            logger_instance = Logger() 
        return logger_instance

    def _resolver_pasta_logs(self) -> Path:
        """Define o caminho onde os logs serão persistidos."""
        try:
            # Tenta usar o path oficial primeiro (G:\memory\logs)
            if os.environ.get("FORCE_FALLBACK_MEMORY", "0") == "1":
                raise RuntimeError("Forcado fallback via env")
            self._subscribers.append(None) # Placeholder para evitar warning na inicialização
            self._path_logs.mkdir(parents=True, exist_ok=True)
            # Teste de escrita simples para validar permissão
            _teste = self._path_logs / ".write_test.tmp"
            with open(_teste, "w", encoding="utf-8") as f:
                f.write("ok")
            _teste.unlink()
            return self._path_logs
        except Exception:
            # Fallback para o caminho local se houver erro de permissão ou path inacessível
            fallback = Path(__file__).resolve().parent.parent / "local_memory" / "logs"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    def register_listener(self, callback: Callable[[Dict], Any]):
        """Permite que outros módulos se inscrevam para receber notificações de log."""
        print(f"[LOGGER]: Novo listener registrado. Total atual: {len(self._subscribers)}")
        # O callback deve ser uma função assíncrona ou um objeto que implemente o método 'handle'.
        self._subscribers.append(ListenerCallback(callback))

    async def _publish_event(self, event_data: Dict):
        """Dispara o evento para todos os listeners registrados."""
        # 1. Persistência (Log File) - Esta parte deve ser rápida e não bloquear o thread principal.
        await self._write_to_file(event_data) # Chamada assíncrona

        # 2. Distribuição de Eventos
        tasks = []
        for listener in self._subscribers:
            try:
                # Assumindo que cada callback pode ser um método assíncrono ou síncrono
                if asyncio.iscoroutinefunction(listener.callback):
                    tasks.append(listener.callback(event_data))
                else:
                    # Se for síncrono, rodamos em executor para não bloquear o loop principal
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, listener.callback, event_data))
            except Exception as e:
                print(f"[LOGGER ERROR]: Falha ao notificar um listener: {e}", file=sys.stderr)

        # Executa todas as notificações em paralelo
        if tasks:
             await asyncio.gather(*tasks, return_exceptions=True)


    async def _write_to_file(self, event_data: Dict):
        """Função interna para escrever o evento no formato JSON Lines."""
        try:
            # Lógica de escrita do arquivo (não precisa ser assíncrona se usar a biblioteca padrão em contexto async)
            # Para simplicidade e robustez, vamos apenas serializar e assumir que é rápido.
            timestamp_str = datetime.fromtimestamp(event_data['timestamp'] / 10**6).strftime('%Y-%m-%d')
            filename = self._path_logs / f"{timestamp_str}.jsonl"

            # Em um ambiente de produção real, usaríamos FileIO assíncrono do sistema operacional.
            with open(filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\\n")

        except Exception as e:
            print(f"[LOGGER ERROR]: Falha ao escrever log em disco ({e}).", file=sys.stderr)


    async def log_event(self, level: Literal['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'], message: str, component: str = "SYSTEM", details: Optional[Dict] = None):
        """Função pública assíncrona para registrar e publicar um evento."""
        if details is None:
            details = {}

        event_data = {
            "timestamp": (datetime.now()).timestamp() * 10**6, # Microsegundos
            "level": level,
            "message": message,
            "component": component,
            "details": details
        }

        # 1. Atualiza o Buffer em Memória
        self.log_buffer_history.append(event_data)

        # 2. Publica e Persiste (A parte assíncrona principal)
        await self._publish_event(event_data)

    # ==================================================================
    #  MÉTODOS PÚBLICOS SÍNCRONOS FIRE-AND-FORGET (BACKWARDS COMPAT)
    #  Mantém a mesma assinatura antiga usada por todos os módulos
    #  hoje: log.info("mensagem", detalhes_dict) etc.
    #  Zero await necessário; funcionam em __init__ e top-level.
    # ==================================================================
    def _montar_e_enfileirar(self, level: Literal['DEBUG','INFO','WARN','ERROR','CRITICAL'], message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        # Normaliza details para Dict: se for str/int/list, põe {valor}
        if details is None:
            details_dict: Dict[str, Any] = {}
        elif isinstance(details, dict):
            details_dict = details
        else:
            try:
                details_dict = {"valor": details}
            except Exception:
                details_dict = {}

        event_data = {
            "timestamp": (datetime.now()).timestamp() * 1_000_000,
            "level": level,
            "message": str(message),
            "component": component,
            "details": details_dict,
        }
        # Atualiza buffer em memória imediatamente
        self.log_buffer_history.append(event_data)
        # Enfileira para o worker thread publicar + persistir de forma async
        if self._worker_loop is not None and self._queue is not None and not self._shutdown_flag:
            try:
                self._worker_loop.call_soon_threadsafe(self._queue.put_nowait, event_data)
            except Exception:
                # Worker morreu ou fila cheia: faz fallback de escrever direto no
                # stdout para não perder o log.
                try:
                    print(f"[LOG FALLBACK {level}][{component}] {message}  details={details_dict!r}", file=sys.stderr)
                except Exception:
                    pass

    def info(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("INFO", message, details, component)

    def warn(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("WARN", message, details, component)

    def warning(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("WARN", message, details, component)

    def error(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("ERROR", message, details, component)

    def debug(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("DEBUG", message, details, component)

    def critical(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("CRITICAL", message, details, component)

    def success(self, message: str, details: Optional[Any] = None, component: str = "SYSTEM") -> None:
        self._montar_e_enfileirar("INFO", message, details, component)


# Inicialização Global do Logger Singleton
# Usa o método _get_instance SÍNCRONO (não requer await) para evitar
# RuntimeWarning "coroutine was never awaited" no import-time
# Todos os arquivos .py do core importam `from core.logger import log`
log = Logger._get_instance()
# Mantemos também o nome `logger` como alias para compatibilidade
# futura caso alguém importe o outro nome por acidente.
logger = log

