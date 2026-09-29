# ============================================================================
# ESPECIALISTA: llm_core (Córtex Geral — LLM Principal)
# FASE DE ATIVAÇÃO: 1 (DIA 1 DA MARATONA 02/10) — JA ESTA ATIVO
#
# Responsabilidade: 95% das respostas do Prometeu passam por aqui.
# Comunica via ollama-python library com o Ollama servindo em http://localhost:11434
# Ollama abstrai llama.cpp + DirectML para a RX 7600 8GB.
# ============================================================================

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import ollama as _ollama_client

from core.base_specialist import (
    BaseSpecialist,
    ResultadoInferencia,
    UsoRecursos,
)
from core.logger import log


class EspecialistaLlmCore(BaseSpecialist):
    """Região cerebral: Córtex Pré-Frontal / Córtex Geral. LLM principal."""

    NOME_INTERNO = "llm_core"
    NOME_HUMANO = "🧠 Córtex Geral (LLM Principal)"
    FASE_ATIVACAO = 1
    DESCRICAO = (
        "Modelo de linguagem geral (Llama 3.1 8B q4_k_m por padrão). "
        "Responsável por conversação, raciocínio, roteamento de ferramentas "
        "e personalidade do Prometeu."
    )

    # Valores padrão (podem ser sobrescritos no __init__)
    # DIA 1: usamos llama3:latest porque já está baixado (4.34GB).
    # Depois que o ollama pull llama3.1:8b (~6GB) acabar, mudar para "llama3.1:8b" abaixo.
    MODELO_PADRAO = "llama3:latest"
    TEMPERATURA_PADRAO = 0.7
    MAX_TOKENS_PADRAO = 1024

    def __init__(self, modelo_override: Optional[str] = None,
                 temperatura: float = TEMPERATURA_PADRAO,
                 max_tokens: int = MAX_TOKENS_PADRAO,
                 ollama_host: str = "http://localhost:11434") -> None:
        super().__init__()
        self.modelo: str = modelo_override or self.MODELO_PADRAO
        self.temperatura: float = temperatura
        self.max_tokens: int = max_tokens
        self._ollama_host: str = ollama_host
        # Cliente ollama-python (não inicializa conexao ainda)
        self._client: Optional[_ollama_client.Client] = None

    # ------------------------------------------------------------------------
    # Ciclo de vida BaseSpecialist (OBRIGATORIOS)
    # ------------------------------------------------------------------------
    def load(self) -> bool:
        """Inicializa o cliente Ollama. Não bloqueia VRAM — Ollama lazy-load."""
        try:
            self._client = _ollama_client.Client(host=self._ollama_host)
            # Teste leve (não baixa/ carrega modelo ainda, só verifica se o server responde)
            try:
                _ = self._client.list()  # /api/tags
            except Exception:
                # Server pode estar fora — não impedimos o load, só avisamos
                log.warn("llm_core_servidor_ollama_offline",
                         {"host": self._ollama_host})
            self._carregado = True
            log.info("llm_core_carregado", {"modelo": self.modelo})
            return True
        except Exception as e:
            self._ultimo_erro = str(e)
            log.error("llm_core_load_falhou", exception=e)
            return False

    def unload(self) -> bool:
        """Descarrega o modelo da VRAM via /api/gpu? (Ollama gerencia por si só)."""
        try:
            # Ollama descarrega sozinho após OLLAMA_KEEP_ALIVE (5s).
            # Nós apagamos apenas a referencia local.
            self._client = None
            self._carregado = False
            return True
        except Exception as e:
            self._ultimo_erro = str(e)
            return False

    def is_loaded(self) -> bool:
        return self._carregado and self._client is not None

    def get_recursos_usados(self) -> UsoRecursos:
        """Estimativa de recursos (VRAM real vem do vram_manager.py)."""
        rec = UsoRecursos()
        rec.modelo_carregado = self.modelo if self._carregado else ""
        return rec

    # ------------------------------------------------------------------------
    # Inferencia real
    # ------------------------------------------------------------------------
    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        """
        Gera uma resposta do LLM.

        Kwargs aceitos (todos opcionais):
            prompt: str           = mensagem nova do usuario (obrigatorio se nao houver historico)
            historico: List[Dict] = lista [{"role":"user"|"assistant","content":"..."}]
            max_tokens: int       = sobrescreve o padrao
            temperatura: float    = sobrescreve o padrao
            sistema: str          = system prompt (ex: "Voce e o Prometeu...")
        """
        t_inicio = time.perf_counter()
        try:
            if not self.is_loaded():
                raise RuntimeError(
                    "Especialista llm_core não carregado. Chame load() antes."
                )
            assert self._client is not None

            prompt: str = kwargs.get("prompt", "")
            historico: List[Dict[str, str]] = list(kwargs.get("historico") or [])
            sistema: Optional[str] = kwargs.get("sistema", None)
            max_tok = int(kwargs.get("max_tokens") or self.max_tokens)
            temp = float(kwargs.get("temperatura") or self.temperatura)

            if not prompt and not historico:
                raise ValueError("prompt ou historico obrigatorios para llm_core.infer()")

            # Monta messages (inclui system se fornecido)
            messages: List[Dict[str, str]] = []
            if sistema:
                messages.append({"role": "system", "content": sistema})
            messages.extend(historico)
            if prompt:
                messages.append({"role": "user", "content": prompt})

            # Chamada real para Ollama
            resposta = self._client.chat(
                model=self.modelo,
                messages=messages,
                stream=False,
                options={
                    "temperature": temp,
                    "num_predict": max_tok,
                },
            )

            # Extrai conteudo e metricas
            conteudo_resposta = str(
                (resposta.get("message") or {}).get("content") or ""
            ).strip()
            tokens_prompt = int((resposta.get("prompt_eval_count") or 0))
            tokens_resposta = int((resposta.get("eval_count") or 0))
            tokens_total = tokens_prompt + tokens_resposta

            resultado = ResultadoInferencia(
                sucesso=True,
                conteudo=conteudo_resposta,
                tempo_ms=round((time.perf_counter() - t_inicio) * 1000, 2),
                tokens_usados=tokens_total,
                modelo_usado=self.modelo,
                metadados={
                    "tokens_prompt": tokens_prompt,
                    "tokens_resposta": tokens_resposta,
                    "temperatura": temp,
                    "max_tokens": max_tok,
                },
            )
            self._registrar_uso(resultado)
            return resultado

        except Exception as e:
            resultado = ResultadoInferencia(
                sucesso=False,
                erro_mensagem=(
                    f"Falha ao gerar resposta no Córtex Geral ({self.modelo}). "
                    f"Verifique se o Ollama está rodando em {self._ollama_host} "
                    f"e se o modelo '{self.modelo}' está baixado (ollama pull {self.modelo})."
                ),
                erro_tecnico=str(e),
                tempo_ms=round((time.perf_counter() - t_inicio) * 1000, 2),
                modelo_usado=self.modelo,
            )
            self._registrar_uso(resultado)
            log.error("llm_core_infer_falhou", exception=e)
            return resultado
