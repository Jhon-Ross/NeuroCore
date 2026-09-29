# ============================================================================
# ESPECIALISTA: llm_code (Área de Broca Tecnológica — Programação)
# FASE DE ATIVAÇÃO: 2 (DIA 2 DA MARATONA — 29/09/2026)
#
# AINDA NÃO ESTÁ ATIVO. Serve como placeholder para a dívida técnica de amanhã.
# Quando ativado: fine-tune / RAG sobre código ou CodeLlama / StarCoder2.
# ============================================================================

from __future__ import annotations

from typing import Any

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos


class EspecialistaLlmCode(BaseSpecialist):

    NOME_INTERNO = "llm_code"
    NOME_HUMANO = "💻 Programador (LLM Código)"
    FASE_ATIVACAO = 2
    DESCRICAO = (
        "Especialista em gerar, revisar e explicar código (Python, Next.js, Rust, "
        "FiveM/VRPEX antigos do Jhon). Ativação planejada: DIA 2 da maratona."
    )

    def load(self) -> bool:
        self._carregado = False
        self._ultimo_erro = self._mensagem_nao_ativado()
        return False

    def unload(self) -> bool:
        self._carregado = False
        return True

    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        return ResultadoInferencia(
            sucesso=False,
            erro_mensagem=self._mensagem_nao_ativado(),
            modelo_usado="(codellama / deepseek-coder — não ativado ainda)",
        )

    def is_loaded(self) -> bool:
        return False

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    # ------------------------------------------------------------------
    @staticmethod
    def _mensagem_nao_ativado() -> str:
        return (
            "🧠 Região CÓDIGO (llm_code) ainda não foi ativada no Prometeu.\n"
            "⏱️  Fase de ativação = DIA 2 da Meta Maratona 02/10 (29/09/2026).\n"
            "📚 Quando ativada: vai analisar, gerar e corrigir código Python / Next.js / Rust "
            "e importar os projetos antigos de FiveM / VRPEX do Jhon para memória RAG pessoal."
        )
