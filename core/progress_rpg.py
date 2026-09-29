# ============================================================================
# MODULO: progress_rpg.py
# SISTEMA RPG DE PROGRESSO ANTI-ABANDONO — Prometeu / NeuroCore
#
# Objetivo: Transformar o desenvolvimento do Prometeu em um RPG de evolucao,
# onde cada acao de codigo, cada resposta correta, cada marco conquistado
# da XP e gera FEITOS (Wall of Wins) visiveis.
#
# Este modulo E A PRIORIDADE 1 do projeto inteiro. Risco Nº1 = abandono por
# falta de motivacao quando o projeto nao parece evoluir. Este modulo resolve
# isso.
#
# Autor: NeuroCore Team
# Linguagem: Comentarios em PT-BR, codigo internacional.
# ============================================================================

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

# ----------------------------------------------------------------------------
# CONSTANTES DE CONFIGURACAO — NUNCA ALTERAR APOS O PRIMEIRO USO
# (se alterar, quebra XP ja acumulado)
# ----------------------------------------------------------------------------

# 7 Habilidades do Prometeu = correspondem as 7 regioes cerebrais especializadas
# Ordem importa para exibicao na UI.
TipoHabilidade = Literal[
    "cortex_geral",    # Córtex Pré-Frontal — LLM geral (llm_core)
    "codigo",          # Área de Broca Tecnológica — Programação (llm_code)
    "audicao",         # Lobos Temporais — Fala para Texto (stt_whisper)
    "fonacao",         # Área de Wernicke Motora — Texto para Fala (tts_xtts)
    "sistema_operacional",  # Córtex Motor SO — Controla Windows/Arquivos
    "visual",          # Lobos Occipitais — Imagem/Visão (image_flux)
    "casa",            # Hipotálamo Doméstico — Casa/IoT (home_control)
]

HABILIDADES_ORDEM: List[TipoHabilidade] = [
    "cortex_geral",
    "codigo",
    "audicao",
    "fonacao",
    "sistema_operacional",
    "visual",
    "casa",
]

HABILIDADES_LABELS: Dict[TipoHabilidade, str] = {
    "cortex_geral":       "🧠 Córtex Geral",
    "codigo":             "💻 Programação",
    "audicao":            "👂 Audição (STT)",
    "fonacao":            "🗣️ Fonação (TTS)",
    "sistema_operacional":"🖱️ Controle SO",
    "visual":             "👁️ Visão (Img)",
    "casa":               "🏠 Casa IoT",
}

HABILIDADES_NOMES_UI: Dict[TipoHabilidade, str] = {
    "cortex_geral":       "Córtex Geral",
    "codigo":             "Código",
    "audicao":            "Audição",
    "fonacao":            "Fonação",
    "sistema_operacional":"S.O.",
    "visual":             "Visual",
    "casa":               "Casa Inteligente",
}

HABILIDADES_ICONES: Dict[TipoHabilidade, str] = {
    "cortex_geral":       "🧠",
    "codigo":             "⚡",
    "audicao":            "👂",
    "fonacao":            "🗣️",
    "sistema_operacional":"🖥️",
    "visual":             "👁️",
    "casa":               "🏠",
}

HABILIDADES_REGIOES: Dict[TipoHabilidade, str] = {
    "cortex_geral":       "llm_core",
    "codigo":             "llm_code",
    "audicao":            "stt_whisper",
    "fonacao":            "tts_xtts",
    "sistema_operacional":"os_control",
    "visual":             "image_flux",
    "casa":               "home_control",
}

HABILIDADES_FASES: Dict[TipoHabilidade, str] = {
    "cortex_geral":       "1/5",
    "codigo":             "2/5",
    "audicao":            "3/5",
    "fonacao":            "3/5",
    "sistema_operacional":"2/5",
    "visual":             "5/5",
    "casa":               "4/5",
}

_EMOJI_FEITOS_POR_TAG: Dict[str, str] = {
    "nascimento":     "🌱",
    "fundacao":       "🌱",
    "primeira_palavra":"💬",
    "codigo":         "⚡",
    "maratona":       "🏁",
    "anti_abandono":  "🛡️",
    "xp":             "⭐",
}

_NOME_FEITO_CURTO_POR_TAG: Dict[str, str] = {
    "nascimento":     "Nascimento",
    "primeira_palavra":"Primeira Palavra",
}

# Formula do Nivel: XP_necessario(N) = N * 100
# Ex: Nível 1 = 100 XP, Nível 2 = 200 XP, ..., Nível 10 = 1000 XP
XP_POR_NIVEL: int = 100
NIVEL_MAXIMO: int = 100  # Teto humano simbolico

# ----------------------------------------------------------------------------
# RESOLUCAO DE CAMINHO DE PERSISTENCIA (com fallback inteligente)
#
# PRIORIDADE 1: G:\memory\prometeu_rpg.json (local oficial permanente, HDD 2TB)
#   — Motivo: evolui por ANOS, nao pode ser apagado com git clean nem formatar SSD
#
# FALLBACK: NeuroCore/local_memory/prometeu_rpg.json (dentro do projeto)
#   — Motivo: Sandbox TRAE / ambientes de dev restritos / G: nao montado
#   — Se cair aqui, printa AVISO CLAREZA no stderr dizendo que o usuario
#     deve copiar manualmente o JSON pra G:\memory quando puder.
# ----------------------------------------------------------------------------
_PASTA_OFICIAL_MEMORIA: Path = Path(r"G:\memory")
_PASTA_FALLBACK_MEMORIA: Path = Path(__file__).resolve().parent.parent / "local_memory"


def _resolver_pasta_memoria() -> Path:
    r"""Testa escrita em G:\memory, se falhar usa fallback no projeto.

    Possui 2 overrides por variavel de ambiente para ambientes restritos
    (como a sandbox TRAE que bloqueia escrita em unidades externas):
      - FORCE_FALLBACK_MEMORY=1 -> pula o teste de G:\ e usa fallback direto
      - OVERRIDE_MEMORY_DIR=X:\caminho -> usa o caminho especificado explicitamente
    """
    import sys

    # Override 1: caminho explicito via env (maior prioridade de todas)
    override_dir = os.environ.get("OVERRIDE_MEMORY_DIR", "").strip()
    if override_dir:
        caminho = Path(override_dir)
        caminho.mkdir(parents=True, exist_ok=True)
        return caminho

    # Override 2: forcado fallback via env (sandbox TRAE / CI)
    if os.environ.get("FORCE_FALLBACK_MEMORY", "0").strip() == "1":
        _PASTA_FALLBACK_MEMORIA.mkdir(parents=True, exist_ok=True)
        print(
            "\nℹ️  FORCE_FALLBACK_MEMORY=1 DETECTADO — SISTEMA RPG\n"
            f"   Pulando teste de escrita em G:\\memory e usando fallback.\n"
            f"   Caminho em uso: {_PASTA_FALLBACK_MEMORIA}\n"
            "   Fora da sandbox, remova esta variavel para usar o HDD oficial.\n",
            file=sys.stderr,
        )
        return _PASTA_FALLBACK_MEMORIA

    # Tenta 1: pasta oficial em G:
    try:
        _PASTA_OFICIAL_MEMORIA.mkdir(parents=True, exist_ok=True)
        _arquivo_teste = _PASTA_OFICIAL_MEMORIA / ".write_test.tmp"
        with open(_arquivo_teste, "w", encoding="utf-8") as f:
            f.write("ok")
        _arquivo_teste.unlink()
        return _PASTA_OFICIAL_MEMORIA
    except Exception:
        # Falhou — cai para fallback e avisa usuario
        _PASTA_FALLBACK_MEMORIA.mkdir(parents=True, exist_ok=True)
        print(
            "\n⚠️  AVISO DE FALLBACK — SISTEMA RPG DO PROMETEU\n"
            f"   Nao foi possivel escrever em {_PASTA_OFICIAL_MEMORIA}\n"
            f"   Dados do RPG serao salvos em: {_PASTA_FALLBACK_MEMORIA}\n"
            "   Quando possivel, mova o arquivo prometeu_rpg.json manualmente\n"
            "   para G:\\memory\\ para evitar perda em caso de git clean.\n",
            file=sys.stderr,
        )
        return _PASTA_FALLBACK_MEMORIA


PASTA_MEMORIA: Path = _resolver_pasta_memoria()
ARQUIVO_RPG: Path = PASTA_MEMORIA / "prometeu_rpg.json"


# ============================================================================
# ESTRUTURAS DE DADOS (schema do JSON persistido)
# ============================================================================

@dataclass
class Habilidade:
    """Uma habilidade individual do Prometeu."""
    nome: TipoHabilidade
    xp_acumulado: int = 0          # XP total historico nesta skill
    xp_para_proximo: int = 100     # Atualizado automaticamente
    nivel_atual: int = 1           # Começa no Nivel 1 (Embrião)
    historico_xp: List[Dict] = field(default_factory=list)  # Log de ganhos

    def xp_restante(self) -> int:
        """Quanto XP falta para o proximo nivel."""
        return max(0, self.xp_para_proximo - self.xp_acumulado)

    def porcentagem_nivel(self) -> float:
        """Progresso 0.0 a 1.0 do nivel atual."""
        if self.xp_para_proximo == 0:
            return 0.0
        falta = self.xp_restante()
        return 1.0 - (falta / self.xp_para_proximo)


@dataclass
class Feito:
    """Marco cronologico na Wall of Wins. Nao pode ser apagado."""
    id: int                           # Auto-incremental
    timestamp_iso: str                # ISO format UTC-3 (ex: 2026-09-28T23:30:00-03:00)
    titulo: str                       # Ex: "Nascimento do Prometeu"
    descricao: str                    # 1 paragrafo detalhado
    habilidade_afetada: Optional[TipoHabilidade]   # Qual skill recebeu XP (pode ser None = marco global)
    xp_concedido: int                 # Quanto XP foi dado neste feito
    tags: List[str] = field(default_factory=list)  # Ex: ["marco_0", "fundacao", "anti_abandono"]


@dataclass
class ProgressoPrometeu:
    """Estado completo do RPG. É o objeto salvo em JSON."""
    versao_schema: int = 1             # Para migracoes futuras
    criado_em_iso: str = ""            # Quando o arquivo foi criado (Nascimento)
    atualizado_em_iso: str = ""        # Ultima escrita em disco
    habilidades: Dict[TipoHabilidade, Habilidade] = field(default_factory=dict)
    feitos: List[Feito] = field(default_factory=list)
    proximo_id_feito: int = 1

    # ------------------------------------------------------------------------
    # Metodos de calculo globais
    # ------------------------------------------------------------------------
    def nivel_global(self) -> int:
        """Media simples dos 7 niveis (arredonda para baixo)."""
        if not self.habilidades:
            return 1
        niveis = [h.nivel_atual for h in self.habilidades.values()]
        return max(1, sum(niveis) // len(niveis))

    def xp_global(self) -> int:
        """Soma de TODO o XP do Prometeu (todas skills)."""
        return sum(h.xp_acumulado for h in self.habilidades.values())

    def total_feitos(self) -> int:
        return len(self.feitos)


# ============================================================================
# CLASSE PRINCIPAL — GerenciadorRPG
# ============================================================================

class GerenciadorRPG:
    """
    Ponto de entrada UNICO para todo o sistema de progresso.
    NUNCA manipule Habilidade/Feito diretamente — sempre passe por aqui.

    Regra de ouro: qualquer operacao que altere estado, chama _salvar()
    automaticamente no final.
    """

    # ------------------------------------------------------------------------
    # Inicializacao e Persistencia
    # ------------------------------------------------------------------------
    def __init__(self, caminho_override: Optional[Path] = None) -> None:
        self.caminho: Path = caminho_override if caminho_override else ARQUIVO_RPG
        self.estado: ProgressoPrometeu = self._carregar_ou_criar()

    def _carregar_ou_criar(self) -> ProgressoPrometeu:
        """Carrega JSON existente ou cria estado virgem com Marco 0."""
        if self.caminho.exists():
            with open(self.caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return self._desserializar(dados)
        else:
            # Primeira vez = NASCIMENTO do Prometeu
            estado_novo = ProgressoPrometeu()
            estado_novo.criado_em_iso = self._agora_iso()
            estado_novo.atualizado_em_iso = estado_novo.criado_em_iso

            # Inicializa as 7 habilidades todas no Nivel 1
            for hab_nome in HABILIDADES_ORDEM:
                estado_novo.habilidades[hab_nome] = Habilidade(nome=hab_nome)

            # Salva imediatamente (antes do Marco 0, para ter arquivo criado)
            self.estado = estado_novo
            self._salvar()

            # Marco 0 = Nascimento (registrado automaticamente)
            self.registrar_feito(
                titulo="Nascimento do Prometeu — Fundação do NeuroCore",
                descricao=(
                    "Dia 0 — A fundação da arquitetura permanente foi concluída. "
                    "Estrutura de pastas definida, documentação na Árvore do Conhecimento, "
                    "e sistema anti-abandono RPG ativado. Este é o dia zero do Prometeu."
                ),
                habilidade_afetada=None,  # Marco global = afeta todas
                xp_concedido=25,
                tags=["marco_0", "fundacao", "nascimento", "anti_abandono"],
            )
            return self.estado

    def _salvar(self) -> None:
        """Persiste estado atual em disco JSON (atomic write)."""
        self.estado.atualizado_em_iso = self._agora_iso()

        # Escreve em .tmp primeiro, depois faz rename (evita corrupcao se crashar no meio)
        tmp_caminho = self.caminho.with_suffix(".tmp")
        with open(tmp_caminho, "w", encoding="utf-8") as f:
            json.dump(self._serializar(), f, ensure_ascii=False, indent=2)
        os.replace(tmp_caminho, self.caminho)

    # ------------------------------------------------------------------------
    # Serializacao <-> Dataclass (simples, sem dependencia de marshmallow)
    # ------------------------------------------------------------------------
    def _serializar(self) -> Dict:
        estado = self.estado
        return {
            "versao_schema": estado.versao_schema,
            "criado_em_iso": estado.criado_em_iso,
            "atualizado_em_iso": estado.atualizado_em_iso,
            "proximo_id_feito": estado.proximo_id_feito,
            "habilidades": {k: asdict(v) for k, v in estado.habilidades.items()},
            "feitos": [asdict(f) for f in estado.feitos],
        }

    def _desserializar(self, dados: Dict) -> ProgressoPrometeu:
        habilidades_dict = dados.get("habilidades", {})
        habilidades_obj: Dict[TipoHabilidade, Habilidade] = {}
        for k, v in habilidades_dict.items():
            habilidades_obj[k] = Habilidade(**v)

        feitos_obj: List[Feito] = []
        for f_dados in dados.get("feitos", []):
            feitos_obj.append(Feito(**f_dados))

        return ProgressoPrometeu(
            versao_schema=dados.get("versao_schema", 1),
            criado_em_iso=dados.get("criado_em_iso", self._agora_iso()),
            atualizado_em_iso=dados.get("atualizado_em_iso", self._agora_iso()),
            habilidades=habilidades_obj,
            feitos=feitos_obj,
            proximo_id_feito=dados.get("proximo_id_feito", 1),
        )

    # ------------------------------------------------------------------------
    # Operacoes PUBLICAS — XP
    # ------------------------------------------------------------------------
    def adicionar_xp(
        self,
        habilidade: TipoHabilidade,
        quantidade: int,
        motivo: str,
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """
        Adiciona XP a uma habilidade. Se passar do nivel, upa automaticamente.

        Args:
            habilidade: Qual das 7 skills recebe XP.
            quantidade: Quantos XP (inteiro positivo).
            motivo: Texto curto explicando POR QUE ganhou XP (exibido na UI).
            tags: Categorizacao opcional.

        Returns:
            Resumo com nivel antigo, novo, levels_upados, etc.
        """
        if quantidade <= 0:
            raise ValueError(f"XP deve ser positivo, recebeu {quantidade}")
        if habilidade not in self.estado.habilidades:
            raise ValueError(f"Habilidade desconhecida: {habilidade}")

        hab = self.estado.habilidades[habilidade]
        nivel_anterior = hab.nivel_atual
        xp_anterior = hab.xp_acumulado

        # 1. Adiciona XP bruto
        hab.xp_acumulado += quantidade

        # 2. Loop de subida de nivel (pode subir varios de uma vez)
        levels_ganhos = 0
        while (
            hab.xp_acumulado >= hab.xp_para_proximo
            and hab.nivel_atual < NIVEL_MAXIMO
        ):
            hab.xp_acumulado -= hab.xp_para_proximo
            hab.nivel_atual += 1
            levels_ganhos += 1
            hab.xp_para_proximo = hab.nivel_atual * XP_POR_NIVEL

        # 3. Log historico dentro da habilidade
        hab.historico_xp.append({
            "timestamp_iso": self._agora_iso(),
            "xp_ganho": quantidade,
            "motivo": motivo,
            "tags": tags or [],
            "levels_ganhos": levels_ganhos,
        })
        # Mantem historico em no maximo 500 entradas (evita JSON gigante em 1 ano)
        if len(hab.historico_xp) > 500:
            hab.historico_xp = hab.historico_xp[-500:]

        self._salvar()

        return {
            "habilidade": habilidade,
            "nivel_anterior": nivel_anterior,
            "nivel_novo": hab.nivel_atual,
            "levels_ganhos": levels_ganhos,
            "xp_anterior": xp_anterior,
            "xp_ganho": quantidade,
            "xp_depois": hab.xp_acumulado,
            "xp_proximo_nivel": hab.xp_para_proximo,
        }

    # ------------------------------------------------------------------------
    # Operacoes PUBLICAS — Feitos (Wall of Wins)
    # ------------------------------------------------------------------------
    def registrar_feito(
        self,
        titulo: str,
        descricao: str,
        habilidade_afetada: Optional[TipoHabilidade],
        xp_concedido: int,
        tags: Optional[List[str]] = None,
    ) -> Feito:
        """
        Registra um marco cronologico IMPORTANTE na Wall of Wins.
        Concede XP automaticamente se habilidade_afetada for especificada.

        Regra: Feitos sao para MARCOS. Para XP diário trivial, use adicionar_xp().
        """
        if not titulo or not descricao:
            raise ValueError("Feito precisa de titulo e descricao.")

        feito = Feito(
            id=self.estado.proximo_id_feito,
            timestamp_iso=self._agora_iso(),
            titulo=titulo,
            descricao=descricao,
            habilidade_afetada=habilidade_afetada,
            xp_concedido=xp_concedido,
            tags=tags or [],
        )

        self.estado.proximo_id_feito += 1
        self.estado.feitos.append(feito)

        # Concede XP ao mesmo tempo se houver habilidade alvo
        if habilidade_afetada is not None and xp_concedido > 0:
            self.adicionar_xp(
                habilidade=habilidade_afetada,
                quantidade=xp_concedido,
                motivo=f"Feito #{feito.id}: {titulo}",
                tags=(tags or []) + ["feito"],
            )
        elif habilidade_afetada is None and xp_concedido > 0:
            # Marco GLOBAL = distribui XP igualmente entre TODAS as 7 habilidades
            xp_por_hab = max(1, xp_concedido // len(HABILIDADES_ORDEM))
            for hab in HABILIDADES_ORDEM:
                self.adicionar_xp(
                    habilidade=hab,
                    quantidade=xp_por_hab,
                    motivo=f"Marco global #{feito.id}: {titulo}",
                    tags=(tags or []) + ["feito", "global"],
                )
        else:
            # Nao tem XP, mas precisa salvar o feito mesmo assim
            self._salvar()

        return feito

    # ------------------------------------------------------------------------
    # Metodos auxiliares de UI
    # ------------------------------------------------------------------------
    def resumo_para_ui(self) -> Dict:
        """Retorna um dict plano pronto para ser serializado e enviado ao Next.js."""
        habilidades_ui: List[Dict] = []
        for hab_nome in HABILIDADES_ORDEM:
            if hab_nome not in self.estado.habilidades:
                continue
            h = self.estado.habilidades[hab_nome]
            habilidades_ui.append({
                "id": hab_nome,
                "nome": HABILIDADES_NOMES_UI.get(hab_nome, hab_nome),
                "nivel": max(0, h.nivel_atual - 1) if hab_nome != "cortex_geral" else h.nivel_atual,
                "xp": h.xp_acumulado,
                "xp_para_prox": h.xp_para_proximo,
                "icone": HABILIDADES_ICONES.get(hab_nome, "🔘"),
                "ativo": hab_nome == "cortex_geral",
                "regiao": HABILIDADES_REGIOES.get(hab_nome, ""),
                "fase": HABILIDADES_FASES.get(hab_nome, "0/5"),
            })

        ultimos_5_feitos_raw = list(reversed(self.estado.feitos[-5:]))

        def _extrair_numero_marco(tags: List[str], feito_id: int) -> int:
            for t in tags or []:
                if t.startswith("marco_"):
                    try:
                        return int(t.split("_", 1)[1])
                    except ValueError:
                        pass
            return max(0, feito_id - 1)

        def _escolher_emoji_feito(tags: List[str], titulo: str) -> str:
            for t in tags or []:
                if t in _EMOJI_FEITOS_POR_TAG:
                    return _EMOJI_FEITOS_POR_TAG[t]
            # Fallback por palavra chave no titulo
            tlow = (titulo or "").lower()
            if "primeira" in tlow or "palavra" in tlow or "chat" in tlow or "resposta" in tlow:
                return "💬"
            if "nascimento" in tlow or "fundacao" in tlow or "arquitetura" in tlow:
                return "🌱"
            if "codigo" in tlow or "código" in tlow or "programacao" in tlow:
                return "⚡"
            return "🏆"

        def _nome_curto_feito(tags: List[str], titulo: str, marco_n: int) -> str:
            for t in tags or []:
                if t in _NOME_FEITO_CURTO_POR_TAG:
                    return _NOME_FEITO_CURTO_POR_TAG[t]
            if "·" in (titulo or ""):
                curto = titulo.split("·", 1)[0].strip()
                if 1 <= len(curto) <= 40:
                    return curto
            # Apenas titulo curto
            return (titulo[:22] + "…") if len(titulo or "") > 25 else (titulo or f"Marco {marco_n}")

        def _formatar_data_br(iso: str) -> str:
            try:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                return dt.strftime("%d/%m/%Y")
            except Exception:
                try:
                    return iso[:10].replace("-", "/")[8:] + "/" + iso[:10].replace("-", "/")[5:7] + "/" + iso[:10].replace("-", "/")[:4]
                except Exception:
                    return iso[:10]

        def _descricao_curta_feito(f_desc: str, tags: List[str]) -> str:
            if "primeira_palavra" in (tags or []):
                return "Primeira resposta: llama3:latest · 409tok · 526ms."
            if "nascimento" in (tags or []) or "fundacao" in (tags or []):
                return "Arquitetura NeuroCore aprovada."
            return (f_desc[:50] + "…") if len(f_desc or "") > 55 else (f_desc or "")

        feitos_ui: List[Dict] = []
        for f in ultimos_5_feitos_raw:
            marco_n = _extrair_numero_marco(f.tags, f.id)
            curto = _nome_curto_feito(f.tags, f.titulo, marco_n)
            feitos_ui.append({
                "id": f.id,
                "nome": f"Marco {marco_n} · {curto}",
                "data": _formatar_data_br(f.timestamp_iso),
                "emoji": _escolher_emoji_feito(f.tags, f.titulo),
                "descricao": _descricao_curta_feito(f.descricao, f.tags),
            })

        xp_total = self.estado.xp_global()
        nivel_global_atual = self.estado.nivel_global()
        xp_prox_nivel = (nivel_global_atual + 1) * XP_POR_NIVEL

        return {
            "nivel_global": nivel_global_atual,
            "xp_total": xp_total,
            "xp_para_proximo_nivel": xp_prox_nivel,
            "total_feitos": self.estado.total_feitos(),
            "habilidades": habilidades_ui,
            "feitos": feitos_ui,
            "atualizado_em_iso": self.estado.atualizado_em_iso,
        }

    def listar_todos_feitos(self, limite: Optional[int] = None) -> List[Dict]:
        """Wall of Wins completa (do mais novo pro mais velho)."""
        feitos_reversos = list(reversed(self.estado.feitos))
        return [
            {
                "id": f.id,
                "data_iso": f.timestamp_iso,
                "titulo": f.titulo,
                "descricao": f.descricao,
                "habilidade_afetada": f.habilidade_afetada,
                "xp_concedido": f.xp_concedido,
                "tags": f.tags,
            }
            for f in (feitos_reversos[:limite] if limite else feitos_reversos)
        ]

    # ------------------------------------------------------------------------
    # Utils internas
    # ------------------------------------------------------------------------
    @staticmethod
    def _agora_iso() -> str:
        """Timestamp ISO com timezone do Brasil (UTC-3) para logs humanos."""
        return datetime.now().astimezone().isoformat(timespec="seconds")


# ============================================================================
# INSTANCIA SINGLETON para o Core usar.
# Qualquer modulo importa 'from core.progress_rpg import rpg' e usa direto.
# ============================================================================
rpg: GerenciadorRPG = GerenciadorRPG()


# ============================================================================
# EXECUCAO MANUAL: Se rodar python progress_rpg.py, mostra o estado atual.
# (para debug rapido no terminal sem precisar do frontend)
# ============================================================================
if __name__ == "__main__":
    estado_ui = rpg.resumo_para_ui()
    print("=" * 70)
    print(f"  PROMETEU RPG  —  Nível Global {estado_ui['nivel_global']}  |  "
          f"{estado_ui['total_feitos']} Feitos  |  "
          f"{estado_ui['xp_global_total']} XP Acumulado")
    print("=" * 70)
    for chave, dados in estado_ui["habilidades"].items():
        barra = "█" * int(dados["porcentagem_nivel"] // 5) + \
                "░" * (20 - int(dados["porcentagem_nivel"] // 5))
        print(f"  {dados['label']:<25} | LVL {dados['nivel_atual']:>3} | "
              f"{barra} | {dados['porcentagem_nivel']:>5}%")
    print("-" * 70)
    print("  Últimos Feitos:")
    for feito in estado_ui["ultimos_feitos"]:
        print(f"    🎖️  [{feito['id']:>3}] {feito['titulo']}  "
              f"(+{feito['xp_concedido']} XP)")
    print("=" * 70)
