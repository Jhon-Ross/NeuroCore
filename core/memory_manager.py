# ============================================================================
# MODULO: memory_manager.py
# MEMORIA DE LONGO PRAZO DO PROMETEU — Backend SQLite ACID
#
# Backend provisório (até fim da maratona 02/10): SQLite3 padrão Python.
# (pós-maratona: migra para Qdrant (vetorial) sem perder nenhum dado.
# Por que SQLite AGORA?
#   1. ACID = não corrompe mesmo com crash de energia.
#   2. Zero dependências externas (built-in no Python 3.12).
#   3. Pesquisa SQL simples = já dá pra fazer buscas full text.
#   4. Migração limpa p/ Qdrant: dump JSON → upsert em batch.
#
# Estratégia anti-corrupção:
#   - Tudo dentro de TRANSACTIONS (BEGIN / COMMIT)
#   - PRAGMA journal_mode=WAL, synchronous=NORMAL (rápido e seguro)
#   - Write-Ahead Log = mesmo crash no meio do COMMIT não corrompe.
#
# Autor: NeuroCore Team
# Linguagem: Comentários em PT-BR.
# ============================================================================

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


# ----------------------------------------------------------------------------
# CAMINHO DO BANCO (fallback como em progress_rpg.py e logger.py)
# ----------------------------------------------------------------------------

_PASTA_OFICIAL_DB: Path = Path(r"G:\memory\sqlite_db")
_PASTA_FALLBACK_DB: Path = Path(__file__).resolve().parent.parent / "local_memory" / "sqlite_db"


def _resolver_pasta_db() -> Path:
    r"""Tenta G:\, senao fallback no projeto."""
    import os
    try:
        if os.environ.get("FORCE_FALLBACK_MEMORY", "0") == "1":
            raise RuntimeError("fallback forcado")
        _PASTA_OFICIAL_DB.mkdir(parents=True, exist_ok=True)
        _t = _PASTA_OFICIAL_DB / ".write_test.tmp"
        with open(_t, "w", encoding="utf-8") as f:
            f.write("ok")
        _t.unlink()
        return _PASTA_OFICIAL_DB
    except Exception:
        _PASTA_FALLBACK_DB.mkdir(parents=True, exist_ok=True)
        return _PASTA_FALLBACK_DB


PASTA_SQLITE: Path = _resolver_pasta_db()
ARQUIVO_DB: Path = PASTA_SQLITE / "prometeu_main.db"


# ============================================================================
# SCHEMA SQL (tabelas permanentes — não remover campos
# ============================================================================

SCHEMA_SQL: str = """
-- ------------------------------------------------------------------
-- Sessões de chat (uma conversa = 1 sessão)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo           TEXT    NOT NULL DEFAULT 'Nova Conversa',
    criado_em        TEXT    NOT NULL,
    atualizado_em    TEXT    NOT NULL,
    metadados_json   TEXT    DEFAULT '{}'  -- tags, contexto, etc
);

-- ------------------------------------------------------------------
-- Mensagens individuais de cada sessão (histórico Prometeu ↔ Usuário)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role             TEXT    NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    conteudo         TEXT    NOT NULL,
    timestamp_iso    TEXT    NOT NULL,
    tokens_usados    INTEGER DEFAULT 0,
    tempo_ms       INTEGER DEFAULT 0,
    metadados_json TEXT    DEFAULT '{}'  -- {modelo, temperatura, etc}
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_time    ON chat_messages(timestamp_iso);

-- ------------------------------------------------------------------
-- Amostras de treinamento do Teacher Model (Ritual Diário)
-- (inputs + saidas + feedback humano do Jhon)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_samples (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo             TEXT    NOT NULL,  -- 'chat_correcao', 'preferencia_estilo', etc
    input_texto        TEXT    NOT NULL,
    output_esperado   TEXT    NOT NULL,
    feedback_humano     TEXT,            -- comentário Jhon Ross (vazio = automático)
    nota_qualidade    INTEGER DEFAULT 5, -- 1 a 10
    origem           TEXT DEFAULT 'ritual_diario',
    usado_no_treino   INTEGER DEFAULT 0,-- 1 = já foi usado para LoRA/RAG
    criado_em        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_training_tipo ON training_samples(tipo);

-- ------------------------------------------------------------------
-- Preferências do usuário (Jhon) — KV store persistente
-- (cor favorita, voz padrão, timezone, etc)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    chave TEXT PRIMARY KEY,
    valor_json TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);

-- ------------------------------------------------------------------
-- Estado do orquestrador / boot (preservado entre reinicios do processo
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_state (
    chave TEXT PRIMARY KEY,
    valor_json TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
"""


# ============================================================================
# CLASSE PRINCIPAL — GerenciadorMemoria
# ============================================================================

class GerenciadorMemoria:
    """Ponto de entrada único para o banco SQLite."""

    def __init__(self, caminho_override: Optional[Path] = None) -> None:
        self.caminho_db: Path = caminho_override if caminho_override else ARQUIVO_DB
        self._lock = threading.RLock()  # SQLite = 1 writer por vez, mas RLock seguro
        self._conn: Optional[sqlite3.Connection] = None
        self._conectar_e_inicializar()

    # ------------------------------------------------------------------------
    # Conexão e inicialização
    # ------------------------------------------------------------------------
    def _conectar_e_inicializar(self) -> None:
        """Abre conexao, seta PRAGMAS (Write-Ahead Log, cria tabelas se não existir."""
        self.caminho_db.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            self.caminho_db,
            check_same_thread=False,  # nosso RLock cuida da seguranca
            timeout=30.0,             # espera até 30s se db estiver lockado
            isolation_level=None,     # nós gerenciamos transactions explicitamente
        )
        assert self._conn is not None
        # WAL = Write Ahead Log (corrupção zero)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        with self._lock:
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()

    @contextmanager
    def _transacao(self) -> Iterator[sqlite3.Connection]:
        """Gerencia BEGIN / COMMIT / ROLLBACK automatico seguro."""
        assert self._conn is not None
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE;")
                yield self._conn
                self._conn.execute("COMMIT;")
            except Exception as e:
                self._conn.execute("ROLLBACK;")
                # Propaga o erro — quem chamou trata
                raise e

    # ------------------------------------------------------------------------
    # Chat Sessions + Messages
    # ------------------------------------------------------------------------
    def criar_sessao_chat(self, titulo: str = "Nova Conversa") -> int:
        """Cria sessao nova, retorna o ID."""
        agora = self._agora()
        with self._transacao() as conn:
            cur = conn.execute(
                "INSERT INTO chat_sessions (titulo, criado_em, atualizado_em) VALUES (?,?,?)",
                (titulo, agora, agora),
            )
            return int(cur.lastrowid)

    def listar_sessoes(self, limite: int = 50) -> List[Dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, titulo, criado_em, atualizado_em, metadados_json "
                "FROM chat_sessions ORDER BY atualizado_em DESC LIMIT ?",
                (limite,),
            )
            return [
                {
                    "id": r[0], "titulo": r[1],
                    "criado_em": r[2], "atualizado_em": r[3],
                    "metadados": json.loads(r[4] or "{}"),
                }
                for r in cur.fetchall()
            ]

    def adicionar_mensagem(
        self,
        session_id: int,
        role: str,
        conteudo: str,
        tokens_usados: int = 0,
        tempo_ms: int = 0,
        metadados: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Insere 1 mensagem e atualiza updated da sessão."""
        if role not in ("user", "assistant", "system", "tool"):
            raise ValueError(f"role invalido: {role}")
        agora = self._agora()
        meta_json = json.dumps(metadados or {}, ensure_ascii=False)
        with self._transacao() as conn:
            cur = conn.execute(
                "INSERT INTO chat_messages "
                "(session_id, role, conteudo, timestamp_iso, "
                " tokens_usados, tempo_ms, metadados_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (session_id, role, conteudo, agora,
                 tokens_usados, tempo_ms, meta_json),
            )
            msg_id = int(cur.lastrowid)
            conn.execute(
                "UPDATE chat_sessions SET atualizado_em = ? WHERE id = ?",
                (agora, session_id),
            )
            return msg_id

    def historico_sessao(self, session_id: int, limite_msg: int = 200,
                        ) -> List[Dict[str, Any]]:
        """Retorna as ultimas N mensagens de uma sessao (mais velhas primeiro)."""
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, role, conteudo, timestamp_iso, tokens_usados, "
                " tempo_ms, metadados_json FROM chat_messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limite_msg),
            )
            rows = list(reversed(cur.fetchall()))
            return [
                {
                    "id": r[0], "role": r[1], "content": r[2],
                    "timestamp_iso": r[3], "tokens_usados": r[4],
                    "tempo_ms": r[5],
                    "metadados": json.loads(r[6] or "{}"),
                }
                for r in rows
            ]

    # ------------------------------------------------------------------------
    # Amostras de treinamento
    # ------------------------------------------------------------------------
    def adicionar_amostra_treinamento(
        self,
        tipo: str,
        input_texto: str,
        output_esperado: str,
        feedback_humano: str = "",
        nota_qualidade: int = 5,
        origem: str = "ritual_diario",
    ) -> int:
        agora = self._agora()
        with self._transacao() as conn:
            cur = conn.execute(
                "INSERT INTO training_samples "
                "(tipo, input_texto, output_esperado, feedback_humano, "
                " nota_qualidade, origem, criado_em) VALUES (?,?,?,?,?,?,?)",
                (tipo, input_texto, output_esperado, feedback_humano,
                 nota_qualidade, origem, agora),
            )
            return int(cur.lastrowid)

    def listar_amostras_nao_usadas(self, limite: int = 100) -> List[Dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, tipo, input_texto, output_esperado, feedback_humano,"
                " nota_qualidade, criado_em FROM training_samples "
                "WHERE usado_no_treino=0 ORDER BY id DESC LIMIT ?",
                (limite,),
            )
            return [
                {"id": r[0], "tipo": r[1], "input": r[2],
                 "output_esperado": r[3], "feedback": r[4],
                 "nota": r[5], "criado_em": r[6]}
                for r in cur.fetchall()
            ]

    # ------------------------------------------------------------------------
    # Preferences + Estado Sistema (KV store)
    # ------------------------------------------------------------------------
    def set_preferencia(self, chave: str, valor: Any) -> None:
        agora = self._agora()
        with self._transacao() as conn:
            conn.execute(
                "INSERT INTO user_preferences(chave, valor_json, atualizado_em) "
                "VALUES(?,?,?) ON CONFLICT(chave) DO UPDATE SET "
                "valor_json=excluded.valor_json, atualizado_em=excluded.atualizado_em",
                (chave, json.dumps(valor, ensure_ascii=False), agora),
            )

    def get_preferencia(self, chave: str, default: Any = None) -> Any:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT valor_json FROM user_preferences WHERE chave=?", (chave,),
            )
            row = cur.fetchone()
            return json.loads(row[0]) if row else default

    def set_estado_sistema(self, chave: str, valor: Any) -> None:
        agora = self._agora()
        with self._transacao() as conn:
            conn.execute(
                "INSERT INTO system_state(chave, valor_json, atualizado_em) "
                "VALUES(?,?,?) ON CONFLICT(chave) DO UPDATE SET "
                "valor_json=excluded.valor_json, atualizado_em=excluded.atualizado_em",
                (chave, json.dumps(valor, ensure_ascii=False), agora),
            )

    def get_estado_sistema(self, chave: str, default: Any = None) -> Any:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT valor_json FROM system_state WHERE chave=?", (chave,),
            )
            row = cur.fetchone()
            return json.loads(row[0]) if row else default

    # ------------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------------
    @staticmethod
    def _agora() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def __del__(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass


# ============================================================================
# SINGLETON
# ============================================================================
memoria: GerenciadorMemoria = GerenciadorMemoria()
