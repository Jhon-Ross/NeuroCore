# ============================================================================
# PACOTE: specialists — 7 Regiões Cerebrais do Prometeu
# (imports são para acesso rápido:
#
#   from specialists import EspecialistaLlmCore, EspecialistaLlmCode, (..
# ============================================================================

from specialists.llm_core import EspecialistaLlmCore
from specialists.llm_code import EspecialistaLlmCode
from specialists.stt_whisper import EspecialistaSttWhisper
from specialists.tts_xtts import EspecialistaTtsXtts
from specialists.os_control import EspecialistaOsControl
from specialists.image_flux import EspecialistaImageFlux
from specialists.home_control import EspecialistaHomeControl

__all__ = [
    "EspecialistaLlmCore",
    "EspecialistaLlmCode",
    "EspecialistaSttWhisper",
    "EspecialistaTtsXtts",
    "EspecialistaOsControl",
    "EspecialistaImageFlux",
    "EspecialistaHomeControl",
]

# Mapa nome_interno -> Classe (para o orquestrador descobrir dinamicamente)
REGIOES_CEREBRAIS = {
    "llm_core": EspecialistaLlmCore,
    "llm_code": EspecialistaLlmCode,
    "stt_whisper": EspecialistaSttWhisper,
    "tts_xtts": EspecialistaTtsXtts,
    "os_control": EspecialistaOsControl,
    "image_flux": EspecialistaImageFlux,
    "home_control": EspecialistaHomeControl,
}
