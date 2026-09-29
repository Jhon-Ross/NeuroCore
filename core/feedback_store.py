# ============================================================================
# MODULO: feedback_store.py
# ARMAZENAMENTO DE FEEDBACK HUMANO DO RITUAL DIARIO
#
# Este modulo e um WRAPPER amigavel sobre o GerenciadorMemoria.
# O banco real e o memory_manager.py (SQLite training_samples).
# Aqui a gente cria helpers para o fluxo especifico do Ritual Diario
# (10 minutos por dia com TRAE + veto do Jhon)
#
# Autor: NeuroCore Team
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.memory_manager import GerenciadorMemoria, memoria as _memoria_default


# ============================================================================
# Tipos de amostra aceitas no Ritual Diario
# ============================================================================
TIPOS_ACEITOS = {
    "chat_correcao":       "Correcao de resposta errada do Prometeu (Jhon reescreveu)",
    "estilo_codigo":       "Preferencia de estilo de codigo (ex: 'comente em PT-BR')",
    "tom_de_voz":           "Tom de voz / personalidade (ex: 'seja mais formal aqui')",
    "preferencia_ui":       "Preferencia visual / layout do painel Next.js",
    "comportamento_so":   "Acao correta no Sistema Operacional / automacao",
    "memoria_pessoal":     "Fato sobre a vida do Jhon que ele quer que eu lembre",
    "outro":               "Feedback generico",
}


@dataclass
class EntradaFeedback:
    """Dados de 1 item do ritual diario."""
    tipo: str
    entrada_original: str
    saida_esperada: str
    comentario_jhon: str
    nota: int  # 1 a 10
    tags: List[str]


class GerenciadorFeedback:
    """
    Helpers para o fluxo do Ritual Diario.

    Uso diario (10 minutos):
        1. O usuario liga TRAE + Prometeu CLI
        2. Jhon revisa ultimas 3-5 amostras
        3. Marca 'isso foi bom / ruim / reescreve assim'
        4. salvar() aqui → grava no training_samples
    """

    def __init__(self, memoria_override: Optional[GerenciadorMemoria] = None) -> None:
        self.mem: GerenciadorMemoria = memoria_override or _memoria_default

    def salvar_ritual_item(
        self,
        tipo: str,
        entrada_original: str,
        saida_esperada: str,
        comentario_jhon: str = "",
        nota_qualidade: int = 7,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Salva 1 amostra do Ritual Diario no banco.

        Returns: id da amostra criada
        """
        if tipo not in TIPOS_ACEITOS:
            tipo = "outro"
        nota = max(1, min(10, nota_qualidade))
        # append tags no comentario (para busca futura)
        comentario_final = comentario_jhon
        if tags:
            comentario_final += f"\n\n[TAGS]: {', '.join(tags)}"
        return self.mem.adicionar_amostra_treinamento(
            tipo=tipo,
            input_texto=entrada_original,
            output_esperado=saida_esperada,
            feedback_humano=comentario_final,
            nota_qualidade=nota,
            origem="ritual_diario",
        )

    def total_amostras_pendentes(self) -> int:
        return len(self.mem.listar_amostras_nao_usadas(limite=10000))

    def estatisticas_ritual(self) -> Dict[str, Any]:
        """Para exibir no painel status."""
        amostras = self.mem.listar_amostras_nao_usadas(limite=10000)
        if not amostras:
            return {
                "total_pendentes": 0,
                "nota_media": 0,
                "por_tipo": {},
            }
        notas = [a["nota"] for a in amostras]
        por_tipo: Dict[str, int] = {}
        for a in amostras:
            por_tipo[a["tipo"]] = por_tipo.get(a["tipo"], 0) + 1
        return {
            "total_pendentes": len(amostras),
            "nota_media": round(sum(notas) / len(notas), 1),
            "por_tipo": por_tipo,
        }

    def marcar_como_usado_no_treinamento(self, ids: List[int]) -> int:
        """Marca um lote de amostras como ja usadas em LoRA/RAG."""
        if not ids:
            return 0
        # TODO: SQL direto via conn (aqui o metodo generico)
        conn = self.mem._conn
        assert conn is not None
        with self.mem._lock:
            cur = conn.executemany(
                "UPDATE training_samples SET usado_no_treino=1 WHERE id=?",
                [(i,) for i in ids],
            )
            conn.commit()
            return cur.rowcount if hasattr(cur, 'rowcount') else len(ids)


# Singleton
feedback_store: GerenciadorFeedback = GerenciadorFeedback()
