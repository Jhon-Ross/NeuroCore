# ============================================================================
# ESPECIALISTA: image_flux (Lobos Occipitais — Visão / Imagem)
# FASE DE ATIVAÇÃO: 5 (PÓS-MARATONA 02/10 ~ Outubro 2026)
#
# Backend futuro: Flux.1-schnell GGUF quantizado Q4 (se couber na RX 7600 8GB)
#   OU Ollama bakllava / minicpm-v (visão) primeiro.
# ============================================================================

from __future__ import annotations

from typing import Any

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos


class EspecialistaImageFlux(BaseSpecialist):

    NOME_INTERNO = "image_flux"
    NOME_HUMANO = "👁️ Visão (Gerar e Interpretar Imagens / Flux.1 + VLM)"
    FASE_ATIVACAO = 5
    DESCRICAO = (
        "Duas funções: (a) Gerar imagens (txt2img = Flux.1-schnell ou similar) "
        "(b) Interpretar imagens existentes (OCR, descrever tela). "
        "Ativação planejada: PÓS-MARATONA, Outubro de 2026."
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
            modelo_usado="(Flux.1 / MiniCPM-V — não ativado ainda)",
        )

    def is_loaded(self) -> bool:
        return False

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    @staticmethod
    def _mensagem() -> str:
        return (
            "👁️ Região VISUAL (image_flux) ainda não foi ativada no Prometeu.\n"
            "⏱️  Fase de ativação = FASE 5 (Outubro de 2026) — após a maratona.\n"
            "🎨 Quando ativada: Prometeu verá a tela do seu computador, "
            "poderá descrever imagens e também gerar artes/concept art via Flux.1 "
            "(ou outro modelo de geração de imagens GGUF que caiba nos 8GB da RX 7600)."
        )
