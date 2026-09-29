# ============================================================================
# ESPECIALISTA: stt_whisper (Lobos Temporais — Audição / Voz → Texto)
# FASE DE ATIVAÇÃO: 3 (DIA 3 DA MARATONA — 30/09/2026)
#
# Backend: faster-whisper (CTranslate2) rodando em CPU ou GPU via DirectML.
# ============================================================================

from __future__ import annotations

from typing import Any

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos


class EspecialistaSttWhisper(BaseSpecialist):

    NOME_INTERNO = "stt_whisper"
    NOME_HUMANO = "👂 Audição (Fala → Texto / Whisper)"
    FASE_ATIVACAO = 3
    DESCRICAO = (
        "Converte voz do microfone / arquivos .wav em texto. "
        "Backend: faster-whisper small/medium em DirectML. "
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
            modelo_usado="(faster-whisper-medium — não ativado ainda)",
        )

    def is_loaded(self) -> bool:
        return False

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    @staticmethod
    def _mensagem() -> str:
        return (
            "👂 Região AUDIÇÃO (stt_whisper) ainda não foi ativada no Prometeu.\n"
            "⏱️  Fase de ativação = DIA 3 da Meta Maratona 02/10 (30/09/2026).\n"
            "🎙️ Quando ativada: Prometeu ouve o microfone e transcreve voz para texto em PT-BR "
            "usando faster-whisper (quantizado CT2 DirectML) na RX 7600."
        )
