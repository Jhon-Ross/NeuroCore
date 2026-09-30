# ============================================================================
# ESPECIALISTA: llm_code (Área de Broca Tecnológica — Programação)
# FASE DE ATIVAÇÃO: 2 (DIA 2 DA MARATONA — 29/09/2026) — ATIVO AGORA
#
# Responsabilidade: gerar, revisar, explicar código.
# Modelo alvo: deepseek-coder:6.7b-instruct-q4_K_M (download em progresso).
# Fallback imediato (enquanto não baixa): llama3:latest (já temos).
# Backend: Ollama (olama-python client), igual llm_core.
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


class EspecialistaLlmCode(BaseSpecialist):
    """Região cerebral: Área de Broca Tecnológica — CÓDIGO."""

    NOME_INTERNO = "llm_code"
    NOME_HUMANO = "💻 Programador (LLM Código)"
    FASE_ATIVACAO = 2
    DESCRICAO = (
        "Especialista em gerar, revisar e explicar código (Python, Next.js, Rust, "
        "projetos antigos FiveM/VRPEX). Ativado DIA 2 da maratona."
    )

    # DIA 2: modelo alvo é deepseek-coder q4_K_M. Enquanto nao baixa, fallback llama3:latest
    # que é garantido estar presente desde o D1.
    MODELO_PADRAO = "deepseek-coder:6.7b-instruct-q4_K_M"
    MODELO_FALLBACK = "llama3:latest"
    TEMPERATURA_PADRAO = 0.2
    MAX_TOKENS_PADRAO = 2048

    # System prompt padrão: pede código limpo, comentários em PT-BR,
    # blocos ```linguagem```, avisa sobre perigos, importa estilo.
    SYSTEM_PROMPT_PADRAO = (
        "Você é o especialista de CÓDIGO do Prometeu (NeuroCore), residente na área de "
        "Broca Tecnológica do cérebro. Regras OBRIGATÓRIAS:\n"
        "1) Escreva código limpo, bem comentado em PORTUGUÊS BRASILEIRO (pt-BR).\n"
        "2) SEMPRE envolva código em blocos ```linguagem``` (ex: ```python```).\n"
        "3) Quando o usuário pedir 'explica', explique linha a linha antes do bloco.\n"
        "4) Avisos de perigo primeiro (ex: 'AÇÃO DESTRUTIVA — confirme antes de rodar').\n"
        "5) Siga o estilo de código do NeuroCore: ABC, type hints, dataclasses, logs estruturados.\n"
        "6) Se não tiver certeza, diga 'Não sei, vamos confirmar' — invente nada.\n"
        "7) COMPATIBILIDADE COM O CODE RUNNER LOCAL (Sandbox 1-Clique):\n"
        "   - Evite usar funções bloqueantes como `input()` que esperam digitação manual no terminal.\n"
        "   - SEMPRE forneça código auto-executável com casos de teste demonstrativos no final (ex: chamando as funções com valores de exemplo e exibindo os resultados via `print()`), para que o usuário veja a saída ao clicar em 'Executar'.\n"
        "   - Se o usuário pedir um aplicativo interativo com botões ou visor (ex: calculadora, jogo, formulário), crie utilizando `tkinter` nativo do Python, com janelas e botões prontos para rodar no Windows.\n"
    )

    def __init__(self,
                 modelo_override: Optional[str] = None,
                 temperatura: float = TEMPERATURA_PADRAO,
                 max_tokens: int = MAX_TOKENS_PADRAO,
                 ollama_host: str = "http://localhost:11434") -> None:
        super().__init__()
        self.modelo_sugerido: str = modelo_override or self.MODELO_PADRAO
        self.modelo_efetivo: str = self.MODELO_FALLBACK   # resolve no load()
        self.temperatura: float = temperatura
        self.max_tokens: int = max_tokens
        self._ollama_host: str = ollama_host
        self._client: Optional[_ollama_client.Client] = None
        self._usou_fallback: bool = False

    # ------------------------------------------------------------------------
    # Ciclo de vida BaseSpecialist (OBRIGATORIOS)
    # ------------------------------------------------------------------------
    def load(self) -> bool:
        """Inicializa cliente Ollama. Descobre qual modelo usar. Fallback se nao tiver deepseek."""
        try:
            self._client = _ollama_client.Client(host=self._ollama_host)
            # Lista modelos disponiveis localmente
            try:
                disponiveis = [m.get("name", "") for m in (self._client.list() or {}).get("models", [])]
            except Exception:
                disponiveis = []
                log.warn("llm_code_servidor_ollama_offline_ou_sem_permissao",
                         {"host": self._ollama_host})

            # Decide modelo:
            if self.modelo_sugerido in disponiveis:
                self.modelo_efetivo = self.modelo_sugerido
                self._usou_fallback = False
            else:
                self.modelo_efetivo = self.MODELO_FALLBACK
                self._usou_fallback = True
                log.warn("llm_code_fallback_para_llama3", {
                    "modelo_sugerido": self.modelo_sugerido,
                    "disponiveis": disponiveis[:10],
                    "motivo": "deepseek-coder ainda não baixado (ollama pull em andamento?)"
                })

            self._carregado = True
            log.info("llm_code_carregado", {
                "modelo_efetivo": self.modelo_efetivo,
                "fallback_usado": self._usou_fallback,
            })
            return True
        except Exception as e:
            self._ultimo_erro = str(e)
            log.error("llm_code_load_falhou", exception=e)
            return False

    def unload(self) -> bool:
        try:
            self._client = None
            self._carregado = False
            return True
        except Exception as e:
            self._ultimo_erro = str(e)
            return False

    def is_loaded(self) -> bool:
        return self._carregado and self._client is not None

    def get_recursos_usados(self) -> UsoRecursos:
        rec = UsoRecursos()
        rec.modelo_carregado = self.modelo_efetivo if self._carregado else ""
        return rec

    # ------------------------------------------------------------------------
    # Inferencia real
    # ------------------------------------------------------------------------
    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        """
        Inferência de código. Kwargs:
            prompt: str                   (obrigatório)
            historico: List[Dict]         ([{role,content}])
            max_tokens, temperatura       (sobrescrevem)
            sistema: str                  (sobrescreve o SYSTEM_PROMPT_PADRAO se dado)
            linguagem: str                (python/ts/typescript/bash etc - injeta dica)
        """
        t_inicio = time.perf_counter()
        try:
            if not self.is_loaded():
                raise RuntimeError("Especialista llm_code não carregado. Chame load() antes.")
            assert self._client is not None

            prompt: str = kwargs.get("prompt", "")
            historico: List[Dict[str, str]] = list(kwargs.get("historico") or [])
            sistema: Optional[str] = kwargs.get("sistema", None) or self.SYSTEM_PROMPT_PADRAO
            max_tok = int(kwargs.get("max_tokens") or self.max_tokens)
            temp = float(kwargs.get("temperatura") or self.temperatura)
            linguagem: Optional[str] = kwargs.get("linguagem", None)

            if linguagem:
                sistema = sistema + f"\n7) De preferência para {linguagem.upper()} nesta resposta.\n"

            if not prompt and not historico:
                raise ValueError("prompt ou historico obrigatorios para llm_code.infer()")

            messages: List[Dict[str, str]] = []
            if sistema:
                messages.append({"role": "system", "content": sistema})
            messages.extend(historico)
            if prompt:
                messages.append({"role": "user", "content": prompt})

            resposta = self._client.chat(
                model=self.modelo_efetivo,
                messages=messages,
                stream=False,
                options={
                    "temperature": temp,
                    "num_predict": max_tok,
                },
            )

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
                modelo_usado=self.modelo_efetivo,
                metadados={
                    "tokens_prompt": tokens_prompt,
                    "tokens_resposta": tokens_resposta,
                    "temperatura": temp,
                    "fallback_usado": self._usou_fallback,
                    "linguagem_sugerida": linguagem or "",
                },
            )
            self._registrar_uso(resultado)
            return resultado

        except Exception as e:
            resultado = ResultadoInferencia(
                sucesso=False,
                erro_mensagem=(
                    f"Falha ao gerar código (modelo {self.modelo_efetivo}). "
                    f"Verifique se o Ollama está rodando em {self._ollama_host}."
                ),
                erro_tecnico=str(e),
                tempo_ms=round((time.perf_counter() - t_inicio) * 1000, 2),
                modelo_usado=self.modelo_efetivo or "",
            )
            self._registrar_uso(resultado)
            log.error("llm_code_infer_falhou", exception=e)
            return resultado

