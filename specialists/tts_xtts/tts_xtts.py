# ============================================================================
# ESPECIALISTA: tts_xtts (Área de Wernicke Motora — Texto → Fala)
# FASE DE ATIVAÇÃO: 3 (DIA 3 DA MARATONA — 30/09/2026)
#
# Backend: Coqui TTS / XTTS v2 (voz PT-BR feminina ou masculina + LoRA voz do Jhon)
# ============================================================================

from __future__ import annotations

from typing import Any

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos


class EspecialistaTtsXtts(BaseSpecialist):

    NOME_INTERNO = "tts_xtts"
    NOME_HUMANO = "🗣️ Fonação (Texto → Fala / XTTS v2)"
    FASE_ATIVACAO = 3
    DESCRICAO = (
        "Converte texto do Prometeu em áudio de voz humana natural em PT-BR. "
        "Backend: Coqui XTTS v2 + clone de voz do Jhon (LoRA). "
        "Ativação: DIA 3 da maratona."
    )

    def load(self) -> bool:
        self._carregado = False
        self._ultimo_erro = self._mensagem()
        return False

    def unload(self) -> bool:
        self._carregado = False
        return True

    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        return ResultadoInferencia(
            sucesso=False,
            erro_mensagem=self._mensagem(),
            modelo_usado="(coqui/XTTS-v2 PT-BR — não ativado ainda)",
        )

    def is_loaded(self) -> bool:
        return False

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    @staticmethod
    def _mensagem() -> str:
        return (
            "🗣️ Região FONAÇÃO (tts_xtts) ainda não foi ativada no Prometeu.\n"
            "⏱️  Fase de ativação = DIA 3 da Meta Maratona 02/10 (30/09/2026).\n"
            "🔊 Quando ativada: Prometeu falará em voz PT-BR humana usando XTTS v2, "
            "com suporte a clone de voz para soar parecido com o Jhon no futuro."
        )
