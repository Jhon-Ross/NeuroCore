# ============================================================================
# MODULO: hybrid_router.py
# ROTEADOR HIBRIDO LOCAL → API EXTERNA (OpenRouter agregador)
#
# Regra de negocio OBRIGATORIA (00-Genese seção 🔀 Hybrid Router):
#   PRIORIDADE 1 = TUDO LOCAL (Ollama na RX 7600) SEMPRE
#   PRIORIDADE 2 = Se LOCAL for REALMENTE impossivel, e o JHON AUTORIZAR,
#                  cai para API externa com TETO MENSAL R$ bloqueavel.
#   NUNCA cai em API "silenciosamente" — SEMPRE avisa o usuário com custo.
#
# No DIA 1 da maratona: o router ESTA DESLIGADO PARA API EXTERNA.
#   → Apenas retorna LOCAL. Isso evita surpresas de custo.
#   → Quando o Jhon configurar OPENROUTER_API_KEY e o teto R$, ativamos.
#
# Autor: NeuroCore Team
# ============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from core.logger import log


class RoteamentoDestino(str, Enum):
    LOCAL = "local"          # Ollama na RX 7600 (GRATIS, PRIVADO 100%)
    API_EXTERNA = "api_ext"  # OpenRouter agregador (custa R$, terceiro)


@dataclass
class DecisaoRoteamento:
    """Decisao do router + proveniencia para logs."""
    destino: RoteamentoDestino
    motivo: str
    custo_estimado_reais: float = 0.0   # só > 0 se destino = API_EXTERNA
    modelo_usar: str = ""               # ex: "llama3.1:8b" / "anthropic/claude-sonnet"
    provedor: str = ""                  # "ollama" / "openrouter"


class HybridRouter:
    """
    Decide CADA INFERENCIA se vai local ou para API.
    No DIA 1: sempre LOCAL (modo TEIMOSO).
    """

    def __init__(self) -> None:
        # Contadores de uso
        self.total_chamadas = 0
        self.total_local = 0
        self.total_api_externa = 0
        self.custo_acumulado_reais_mes: float = 0.0

        # ---- CONFIGURACAO TETO MENSAL ----
        # (estes valores virao de user_preferences no futuro)
        # Hoje = 0.0 R$ = BLOQUEADO TOTALMENTE (modo seguro padrão)
        self.teto_mensal_reais: float = float(
            os.environ.get("PROMETEU_TETO_MENSAL_REAIS", "0.0") or "0.0"
        )
        # Chave OpenRouter = se vazia, API externa FICA DESLIGADA
        self._openrouter_api_key: str = (
            os.environ.get("OPENROUTER_API_KEY", "") or ""
        ).strip()

        self._modo_force_local: bool = (
            self._openrouter_api_key == "" or self.teto_mensal_reais <= 0.0
        )
        log.info("hybrid_router_iniciado", self._estado_dict())

    # ------------------------------------------------------------------
    # API Publica
    # ------------------------------------------------------------------
    def decidir(self,
                habilidade_alvo: str = "cortex_geral",
                urgencia_maxima: bool = False,
                forcar_api_externa: bool = False,
                ) -> DecisaoRoteamento:
        """
        Decide destino para a próxima inferência.

        Args:
            habilidade_alvo:  qual especialista / região chamou
            urgencia_maxima:  se True, pode cair API se local estiver lento
            forcar_api_externa: SÓ ACEITAMOS se JHON confirmar via CLI/UI
        """
        self.total_chamadas += 1
        # CASO 1 (99,99% dos casos DIA 1): API externa DESLIGADA → LOCAL
        if self._modo_force_local and not forcar_api_externa:
            self.total_local += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.LOCAL,
                motivo=(
                    "Modo TEIMOSO DIA1: HybridRouter SEMPRE LOCAL "
                    "(OpenRouter nao configurado OU teto mensal R$0,00)."
                ),
                modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                provedor="ollama",
            )

        # CASO 2: usuario FORCOU via flag (ex: urgencia)
        if forcar_api_externa:
            if not self._pode_usar_api():
                self.total_local += 1
                return DecisaoRoteamento(
                    destino=RoteamentoDestino.LOCAL,
                    motivo=(
                        "Usuario pediu API externa mas TETO R$ estourado OU "
                        "OPENROUTER_API_KEY vazia. Caiu para LOCAL para segurança."
                    ),
                    modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                    provedor="ollama",
                )
            # Deixa ir (custara caro):
            self.total_api_externa += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.API_EXTERNA,
                motivo="Usuário forçou API externa explicitamente.",
                custo_estimado_reais=0.03,
                modelo_usar="anthropic/claude-sonnet-4o",
                provedor="openrouter",
            )

        # CASO 3: decisao heuristica padrão (dia 2+)
        # → ainda nao implementado, cai LOCAL por segurança
        self.total_local += 1
        return DecisaoRoteamento(
            destino=RoteamentoDestino.LOCAL,
            motivo="Heuristica padrão: LOCAL primeiro, API externa só por necessidade.",
            modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
            provedor="ollama",
        )

    # ------------------------------------------------------------------
    # Helpers publicos
    # ------------------------------------------------------------------
    def modelo_local_padrao_para(self, habilidade: str) -> str:
        """Diz qual modelo local usar p/ cada habilidade."""
        if habilidade == "codigo":
            return "qwen2.5-coder:7b"      # baixa se nao existir ainda, fallback llama3
        return "llama3.1:8b"                # padrao geral

    def _pode_usar_api(self) -> bool:
        """True = tem chave E ainda nao estourou teto do mes."""
        if not self._openrouter_api_key:
            return False
        return self.custo_acumulado_reais_mes < self.teto_mensal_reais

    def _estado_dict(self) -> Dict[str, Any]:
        return {
            "modo_force_local": self._modo_force_local,
            "openrouter_key_configurada": bool(self._openrouter_api_key),
            "teto_mensal_reais": self.teto_mensal_reais,
            "gasto_atual_mes_reais": round(self.custo_acumulado_reais_mes, 2),
        }


# Singleton global
hybrid_router: HybridRouter = HybridRouter()
