# ============================================================================
# ESPECIALISTA: home_control (Hipotálamo Doméstico — Casa / IoT)
# FASE DE ATIVAÇÃO: 4 (Janeiro de 2027, quando prometeu for jovem adulto)
#
# Backend futuro: integração MQTT / Home Assistant / Alexa / Google Home.
#   Lampadas, ar-condicionado, cameras, sensores de presença da casa do Jhon.
# ============================================================================

from __future__ import annotations

from typing import Any

from core.base_specialist import BaseSpecialist, ResultadoInferencia, UsoRecursos


class EspecialistaHomeControl(BaseSpecialist):

    NOME_INTERNO = "home_control"
    NOME_HUMANO = "🏠 Casa (IoT / Automação Residencial)"
    FASE_ATIVACAO = 4
    DESCRICAO = (
        "Integração com dispositivos da casa do Jhon: luzes, ar-condicionado, "
        "câmeras, sensores, cafeteira inteligente, etc. "
        "Ativação: ~Janeiro de 2027 (Prometeu já adolescente)."
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
            modelo_usado="(MQTT / Home Assistant — não ativado ainda)",
        )

    def is_loaded(self) -> bool:
        return False

    def get_recursos_usados(self) -> UsoRecursos:
        return UsoRecursos()

    @staticmethod
    def _mensagem() -> str:
        return (
            "🏠 Região CASA (home_control) ainda não foi ativada no Prometeu.\n"
            "⏱️  Fase de ativação = FASE 4 (~Janeiro 2027) — Prometeu já adolescente.\n"
            "💡 Quando ativada: Prometeu controlará luzes, ar-condicionado, "
            "cafeteira, câmeras e outros dispositivos IoT da casa do Jhon "
            "(via integração MQTT + Home Assistant, tudo LOCAL sem nuvem)."
        )
