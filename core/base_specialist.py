# ============================================================================
# MODULO: base_specialist.py
# CONTRATO (INTERFACE) COMUM PARA TODAS AS REGIOES CEREBRAIS DO PROMETEU
#
# Todas as 7 especializações (llm_core, llm_code, stt_whisper, tts_xtts,
# os_control, image_flux, home_control) OBRIGATORIAMENTE herdam desta classe.
#
# Por que isso existe? (Anti-divida-tecnica: garante que daqui a 6 meses,
# quando adicionarmos a 8ª região (ex: robotica_humanoide) ela encaixa
# perfeitamente sem reescrever o orquestrador. NENHUMA linha do
# orquestrador pode fazer if/else por tipo de especialista.
#
# Autor: NeuroCore Team
# Linguagem: Comentarios em PT-BR, codigo internacional.
# ============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


# ============================================================================
# DATACLASSES AUXILIARES (schema de retorno padronizado)
# ============================================================================

@dataclass
class ResultadoInferencia:
    """
    Schema UNICO de retorno de TODAS as chamadas a um especialista.

    O orquestrador LangGraph sempre recebe um objeto deste tipo,
    independente de qual especialista foi chamado. Isso elimina 90%
    dos try/except no core.
    """
    sucesso: bool                                # True = deu tudo certo, False = tratavel
    conteudo: Any = None                         # O resultado real da inferencia
    erro_mensagem: Optional[str] = None         # Se sucesso=False, motivo humano
    erro_tecnico: Optional[str] = None        # Se sucesso=False, stacktrace tecnico
    tempo_ms: float = 0.0                       # Tempo gasto em ms (para painel status)
    tokens_usados: int = 0                   # Total tokens (LLM, audio duracao, etc
    modelo_usado: Optional[str] = None            # Qual modelo/versao foi usado
    metadados: Dict[str, Any] = field(default_factory=dict)  # Dados especiais livres
    timestamp_iso: str = field(
        default_factory=lambda: datetime.now().astimezone().isoformat(timespec="seconds")
    )

    @property
    def resumo_curto(self) -> str:
        """Representacao textual curta para logs."""
        status = "✅" if self.sucesso else "❌"
        return (
            f"{status} [{self.tempo_ms:.0f}ms | "
            f"modelo={self.modelo_usado} | "
            f"tokens={self.tokens_usados}"
        )


@dataclass
class UsoRecursos:
    """Snapshot dos recursos consumidos por um especialista carregado."""
    vram_mb: int = 0            # VRAM da GPU usada (se aplica)
    ram_mb: int = 0             # RAM do sistema usada
    cpu_pct: float = 0.0        # CPU média (0-100)
    modelo_carregado: str = ""  # Nome humano do modelo em memoria


# ============================================================================
# CLASSE BASE — BaseSpecialist (ABC)
# ============================================================================

class BaseSpecialist(ABC):
    """
    Classe ABSTRATA. NUNCA instancie diretamente.

    Ciclo de vida padrao de TODO especialista:
        1. __init__()      → configurar caminhos, configuracao (LEVE, nao carrega modelo)
        2. load()         → carrega modelo pesado em VRAM/RAM (CHAMADO PELO VRAM_MANAGER)
        3. infer()        → 1 ou N chamadas (uso real (vai variar por tipo)
        4. unload()       → descarrega da memoria (CHAMADO PELO VRAM_MANAGER antes de carregar o proximo)

    A troca de especialistas é OBRIGATORIAMENTE passando por estes 4 passos,
    pois a RX 7600 tem so 8GB de VRAM. Impossivel ter 2 LLMs grandes.
    """

    # ------------------------------------------------------------------------
    # ATRIBUTOS QUE CADA ESPECIALISTA DEVE SOBRESCREVER
    # ------------------------------------------------------------------------
    NOME_INTERNO: str = "especialista_base"  # id unico, ex: "llm_core", "stt_whisper"
    NOME_HUMANO: str = "Especialista Base"
    FASE_ATIVACAO: int = 99               # 1=Dia1, 2=Dia2, 3=Dia3, 4=Dia4, 5+=Pos-Maratona
    DESCRICAO: str = "Classe base, sem funcao"

    # ------------------------------------------------------------------------
    # Estado interno (gerenciado pelos metodos)
    # ------------------------------------------------------------------------
    def __init__(self) -> None:
        self._carregado: bool = False
        self._ultimo_erro: Optional[str] = None
        self._config: Dict[str, Any] = {}
        # Todo especialista tem o proprio contador de uso (para painel estatisticas)
        self.total_chamadas: int = 0
        self.tempo_total_ms: float = 0.0
        self.tokens_total: int = 0

    # ========================================================================
    # METODOS ABSTRATOS — OBRIGATORIO IMPLEMENTAR EM CADA FILHO
    # ========================================================================

    @abstractmethod
    def load(self) -> bool:
        """
        Carrega modelos pesados (arquivos GGUF/CT2/pesos na VRAM.

        Regras de implementacao:
        - NUNCA de exception. Sempre retorne True/False.
        - Se sucesso: sete self._carregado = True e retorne True
        - Se falhar: sete self._ultimo_erro e retorne False
        - Deve ser IDEMPOTENTE: chamar load() 2x seguidas nao crasha.
        """
        ...

    @abstractmethod
    def unload(self) -> bool:
        """
        Descarrega tudo da memoria (VRAM e RAM).

        Regras:
        - Libera TUDO (del, gc.collect(), torch.cuda.empty_cache() se aplicavel
        - Seta self._carregado = False
        - Idempotente: chamar 2x nao crasha
        - NUNCA de exception
        """
        ...

    @abstractmethod
    def infer(self, **kwargs: Any) -> ResultadoInferencia:
        """
        Executa a funcao principal do especialista.

        Args (varia por tipo de especialista):
          - llm_core:  prompt: str, historico: List[Dict], max_tokens: int
          - stt_whisper: caminho_audio: Path | bytes
          - tts_xtts: texto: str, voz_id: str
          - etc.

        Retorna SEMPRE um ResultadoInferencia (nunca None, nunca exception).
        Use try/except DENTRO deste metodo e converta qualquer crash em
        ResultadoInferencia(sucesso=False, ...).
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Retorna True se o especialista esta 100% pronto para infer()."""
        ...

    @abstractmethod
    def get_recursos_usados(self) -> UsoRecursos:
        """
        Retorna snapshot atual de VRAM/RAM/CPU usados.
        Se especialista nao usa VRAM, retorne 0 em vram_mb.
        """
        ...

    # ========================================================================
    # METODOS CONCRETOS (herdados por todos — nao precisa reimplementar)
    # ========================================================================

    def get_estado(self) -> Dict[str, Any]:
        """Estado resumido do especialista (para enviar ao painel status)."""
        return {
            "nome_interno": self.NOME_INTERNO,
            "nome_humano": self.NOME_HUMANO,
            "fase_ativacao": self.FASE_ATIVACAO,
            "carregado": self._carregado,
            "ultimo_erro": self._ultimo_erro,
            "estatisticas": {
                "total_chamadas": self.total_chamadas,
                "tempo_total_ms": round(self.tempo_total_ms, 2),
                "tokens_total": self.tokens_total,
                "tempo_medio_ms": (
                    round(self.tempo_total_ms / self.total_chamadas, 2)
                    if self.total_chamadas > 0 else 0.0
                ),
            },
        }

    def _registrar_uso(self, resultado: ResultadoInferencia) -> None:
        """Chamado PELOS FILHOS no final de infer() para estatisticas."""
        self.total_chamadas += 1
        self.tempo_total_ms += resultado.tempo_ms
        self.tokens_total += resultado.tokens_usados

    def __repr__(self) -> str:
        status = "CARREGADO" if self._carregado else "DESCARREGADO"
        return f"<BaseSpecialist:{self.NOME_INTERNO} {status} chamadas={self.total_chamadas}>"
