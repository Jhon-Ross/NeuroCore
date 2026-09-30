# ============================================================================
# MODULO: hybrid_router.py
# ROTEADOR HIBRIDO LOCAL → API EXTERNA (OpenRouter agregador, Anthropic Claude direto, Google Gemini direto)
#
# Regra de negocio OBRIGATORIA (00-Genese seção 🔀 Hybrid Router):
#   PRIORIDADE 1 = TUDO LOCAL (Ollama na RX 7600) SEMPRE.
#   PRIORIDADE 2 = Se LOCAL for REALMENTE impossivel, e o JHON AUTORIZAR,
#                  cai para API externa com TETO MENSAL R$ bloqueavel.
#   NUNCA cai em API "silenciosamente" — SEMPRE avisa o usuário com custo.
#
# PADRÃO ATUAL: HybridRouter ESTA DESLIGADO PARA API EXTERNA.
#   → Apenas retorna LOCAL. Isso evita surpresas de custo.
#   → Para ligar: preencha 1 (ou mais) chaves em .env E set PROMETEU_TETO_MENSAL_REAIS > 0.
#   → Exemplo chaves: OPENROUTER_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY
#
# Autor: NeuroCore Team
# ============================================================================

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# CARREGADOR MANUAL DO .env (NÃO depende de python-dotenv pip)
# Garante que ANTES do singleton HybridRouter ser criado, as variáveis
# de ambiente (chaves, teto, etc.) existam em os.environ. Usa setdefault:
# NÃO sobreescreve se já existir no shell.
# ---------------------------------------------------------------------------
_CAMINHO_ENV_HR = Path(__file__).resolve().parent.parent / ".env"
if _CAMINHO_ENV_HR.exists():
    with open(_CAMINHO_ENV_HR, "r", encoding="utf-8") as _fenv:
        for _ln in _fenv:
            _ln = _ln.strip()
            if not _ln or _ln.startswith("#") or "=" not in _ln:
                continue
            _k, _, _v = _ln.partition("=")
            _k = _k.strip()
            _v = _v.strip().strip("\"'")
            if _k and _v:
                os.environ.setdefault(_k, _v)

from core.logger import log


class RoteamentoDestino(str, Enum):
    LOCAL = "local"          # Ollama na RX 7600 (GRATIS, PRIVADO 100%)
    API_EXTERNA = "api_ext"  # Qualquer provider externo listado abaixo


class ProviderExterno(str, Enum):
    """Providers externos suportados. Ordem de preferência = ordem aqui."""
    OPENROUTER = "openrouter"    # Agregador: 1 chave → GPT, Claude, Gemini +100 outros
    ANTHROPIC = "anthropic"      # Chave direta Anthropic. Usa modelo claude-3-5-sonnet-20241022.
    GEMINI = "gemini"            # Chave direta Google Gemini. Usa modelo gemini-3.5-flash-lite (camada gratuita).


@dataclass
class DecisaoRoteamento:
    """Decisao do router + proveniencia para logs."""
    destino: RoteamentoDestino
    motivo: str
    custo_estimado_reais: float = 0.0   # só > 0 se destino = API_EXTERNA
    modelo_usar: str = ""               # ex: "llama3.1:8b" / "claude-3-5-sonnet-20241022" / "anthropic/claude-sonnet"
    provedor: str = ""                  # "ollama" / "openrouter" / "anthropic" / "gemini"
    erro_provedor: Optional[str] = None # mensagem de erro se provider escolhido nao tem chave


class HybridRouter:
    """
    Decide CADA INFERENCIA se vai local ou para API.
    PADRÃO HOJE: SEMPRE LOCAL (modo TEIMOSO) a MENOS que 3 condições sejam VERDADEIRAS SIMULTANEAMENTE:
      1. O Jhon autorizou explicitamente nesta chamada → forcar_api_externa=True.
      2. Tem pelo menos 1 provider EXTERNO com chave configurada em .env.
      3. custo_acumulado_do_mes < teto_mensal_reais (não estourou o cartão).
    """

    def __init__(self) -> None:
        # Contadores de uso
        self.total_chamadas = 0
        self.total_local = 0
        self.total_api_externa = 0
        self.custo_acumulado_reais_mes: float = 0.0

        # ---- CONFIGURACAO TETO MENSAL ----
        # (estes valores virão de user_preferences no futuro)
        # Hoje = 0.0 R$ = BLOQUEADO TOTALMENTE (modo seguro padrão).
        # Mesmo que chaves existam, se teto <= 0 → TUDO LOCAL SEMPRE.
        self.teto_mensal_reais: float = float(
            os.environ.get("PROMETEU_TETO_MENSAL_REAIS", "0.0") or "0.0"
        )

        # ---- CHAVES PROVIDERS EXTERNOS (LIDAS DE .env, NUNCA hardcoded) ----
        # Ordem de preferência: OpenRouter (mais flexível) → Anthropic direto → Gemini.
        self._chaves: Dict[ProviderExterno, str] = {
            ProviderExterno.OPENROUTER: (os.environ.get("OPENROUTER_API_KEY", "") or "").strip(),
            ProviderExterno.ANTHROPIC: (os.environ.get("ANTHROPIC_API_KEY", "") or "").strip(),
            ProviderExterno.GEMINI:    (os.environ.get("GEMINI_API_KEY", "") or "").strip(),
        }

        # Modelo padrão que vai ser usado por cada provider, caso ele seja selecionado.
        self._modelos_padrao: Dict[ProviderExterno, str] = {
            ProviderExterno.OPENROUTER: "anthropic/claude-sonnet-4o",
            ProviderExterno.ANTHROPIC:  "claude-3-5-sonnet-20241022",
            ProviderExterno.GEMINI:     "gemini-3.5-flash-lite",
        }

        # ================================================================
        # PERFIL INTELIGENTE DE CADA PROVIDER (usado na decisão POR TAREFA)
        # Valores são estimativas empíricas, ajustáveis via .env mais adiante.
        # São USADOS PARA COMPARAR e BALANCEAR, não para bloquear nada.
        # ================================================================
        self._perfil_provider: Dict[ProviderExterno, Dict[str, Any]] = {
            ProviderExterno.ANTHROPIC: {
                "custo_nominal_por_1k_tokens_brl": 0.030,  # caro
                "velocidade_esperada_ms_por_400_out": 4500,  # médio (claude 3.5 sonnet)
                "forcas": {"codigo_avancado", "raciocinio_logico", "arquitetura_sistema", "code_review", "matematica", "planejamento_longo_prazo"},
                "fraquezas": {"respostas_rapidas_curtas", "baixissimo_custo"},  # bom mas demora mais e é caro
            },
            ProviderExterno.GEMINI: {
                "custo_nominal_por_1k_tokens_brl": 0.000,  # camada gratuita flash-lite (hoje)
                "velocidade_esperada_ms_por_400_out": 3000,  # ~30% mais rápido que claude 3.5
                "forcas": {"resposta_rapida", "explicacoes_simple", "sumarizacao", "dados_em_tabela", "perguntas_gerais", "texto_grande_analise"},
                "fraquezas": {"raciocinio_profundo_ordem_superior"},  # flash-lite é mais superficial
            },
            ProviderExterno.OPENROUTER: {
                "custo_nominal_por_1k_tokens_brl": 0.025,  # intermediário
                "velocidade_esperada_ms_por_400_out": 6000,  # mais lento (pula pelo agregador)
                "forcas": {"variedade_modelos", "fallback_multiplos_providers", "acesso_gpt", "acesso_gemini_alta_qualidade"},
                "fraquezas": {"latencia", "complexidade_extra_fallback"},
            },
        }

        # Estratégia de BALANCEAMENTO Round-Robin por CATEGORIA de tarefa.
        # Quando 2 ou mais providers têm SCORE IGUAL na mesma tarefa, nós
        # ROTACIONAMOS para garantir uso DISTRIBUÍDO (não monopólio Anthropic).
        # Ex.: tarefa "pergunta simples" (Gemini + Anthropic ambos ≥60) →
        #      1º pedido: Gemini, 2º pedido: Anthropic, 3º: Gemini etc.
        self._rr_por_categoria: Dict[str, int] = {
            "codigo_avancado": 0,
            "resposta_simples": 0,
            "analise_grande_texto": 0,
            "arquitetura_planejamento": 0,
            "geral": 0,
        }

        # MODO FORCE LOCAL = ATIVO se:
        #   (a) teto mensal <= 0  OU
        #   (b) NENHUM provider tem chave configurada.
        # Esta é a proteção dupla: mesmo usuário colocando chave por engano sem teto → bloqueia.
        self._modo_force_local: bool = (
            self.teto_mensal_reais <= 0.0 or self._n_tem_nenhuma_chave()
        )
        log.info("hybrid_router_iniciado", self._estado_dict())

    # ------------------------------------------------------------------
    # API Publica
    # ------------------------------------------------------------------
    def decidir(self,
                habilidade_alvo: str = "cortex_geral",
                urgencia_maxima: bool = False,
                forcar_api_externa: bool = False,
                override_provider: str | None = None,
                heuristica_escolha_automatica: bool = False,
                texto_da_pergunta: str = "",
                ) -> DecisaoRoteamento:
        """
        Decide destino para a próxima inferência.

        Args:
            habilidade_alvo:           qual especialista / região chamou
            urgencia_maxima:           se True, pode cair API se local estiver lento
            forcar_api_externa:        LEGACY. Mantido para compatibilidade.
            override_provider:         NOVO. Valores: None/"auto"/"local"/"openrouter"/"anthropic"/"gemini"
                                         - "auto" = heuristica Prometeu decide (heuristica_escolha_automatica=True)
                                         - "local" = FORÇA Ollama, ignora chave existente
                                         - "openrouter"/"anthropic"/"gemini" = FORÇA provider especifico (se chave + teto ok)
                                         - None = comportamento padrão (LOCAL hoje, com fallback para heurística)
            heuristica_escolha_automatica: NOVO. Quando True + override_provider="auto",
                                         o Prometeu analisa texto_da_pergunta e decide QUAL MELHOR
                                         provider (LOCAL por padrão; API só para tarefas de alta complexidade).
            texto_da_pergunta:         NOVO. String bruta do usuário, usada na heurística automática.
        """
        self.total_chamadas += 1

        # ==============================================================
        # CASO 0: USUÁRIO ESCOLHEU "🧠 OLLAMA LOCAL" (override_provider == "local")
        #   → VAI SEMPRE LOCAL, PODE PARAR AQUI. Força total. NÃO PASSA por nenhuma
        #     verificação de chave ou teto.
        # ==============================================================
        if override_provider == "local":
            self.total_local += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.LOCAL,
                motivo=(
                    "Usuário selecionou explicitamente 'Ollama RX 7600 (Local)' no dropdown. "
                    "Tudo local, sem custo, sem risco."
                ),
                modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                provedor="ollama",
            )

        # ==============================================================
        # CASO 1: OVERRIDE PROVIDER ESPECÍFICO (anthropic / openrouter / gemini)
        #   → Usuário clicou no dropdown e escolheu um provider direto.
        #   → Tentamos usar ele. Se falhar (sem chave / teto estourado),
        #     CAI PARA LOCAL POR SEGURANÇA, com aviso claro no `motivo`.
        # ==============================================================
        if override_provider in ("anthropic", "openrouter", "gemini"):
            prov_codigo = ProviderExterno(override_provider)
            tem_chave = len(self._chaves.get(prov_codigo, "").strip()) > 0
            if tem_chave and self.teto_mensal_reais > 0 and self.custo_acumulado_reais_mes < self.teto_mensal_reais:
                self.total_api_externa += 1
                return DecisaoRoteamento(
                    destino=RoteamentoDestino.API_EXTERNA,
                    motivo=(
                        f"Usuário selecionou explicitamente '{override_provider}' no dropdown. "
                        f"Teto R${self.teto_mensal_reais:.2f} ainda disponível. "
                        f"Executando via provider externo."
                    ),
                    custo_estimado_reais=0.03,
                    modelo_usar=self._modelos_padrao[prov_codigo],
                    provedor=override_provider,
                )
            # Falhou segurança → cai LOCAL
            falta_que = []
            if not tem_chave:
                falta_que.append(f"chave {prov_codigo.value.upper()} NÃO configurada em .env")
            if self.teto_mensal_reais <= 0:
                falta_que.append("TETO MENSAL = R$0,00 (bloqueado)")
            elif self.custo_acumulado_reais_mes >= self.teto_mensal_reais:
                falta_que.append(f"TETO MENSAL de R${self.teto_mensal_reais:.2f} ESTOUROU (gasto atual = R${self.custo_acumulado_reais_mes:.2f})")
            self.total_local += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.LOCAL,
                motivo=(
                    f"Usuário escolheu '{override_provider}' mas a proteção ativou: "
                    f"{'; '.join(falta_que)}. "
                    f"Caiu para Ollama LOCAL por segurança para não quebrar a conversa."
                ),
                modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                provedor="ollama",
                erro_provedor="; ".join(falta_que) if falta_que else None,
            )

        # ==============================================================
        # CASO 2: HEURÍSTICA AUTOMÁTICA (override_provider == "auto" OU None +
        #         heuristica_escolha_automatica == True)
        #   → PROMETEU decide usando SCORE PONDERADO (categoria_tarefa × custo ×
        #     velocidade × diversificação), não mais hardcoded Anthropic sempre.
        #   → Em caso de empate ±5pts, faz ROUND-ROBIN POR CATEGORIA para BALANCEAR
        #     o uso das APIs que o Jhon tem chave.
        # ==============================================================
        if override_provider == "auto" or (override_provider is None and heuristica_escolha_automatica):
            if self._pode_usar_api():
                prov_heuristica = self._heuristica_automatica_escolhe_provider(
                    habilidade_alvo, texto_da_pergunta
                )
                if prov_heuristica is not None:
                    self.total_api_externa += 1
                    perfil = self._perfil_provider.get(prov_heuristica, {})
                    custo_1k = perfil.get("custo_nominal_por_1k_tokens_brl", 0.0)
                    vel_ms = perfil.get("velocidade_esperada_ms_por_400_out", 0)
                    motivos_detalhes: List[str] = []
                    forcas = perfil.get("forcas", set())
                    if forcas:
                        motivos_detalhes.append(f"pontos_fortes: {', '.join(sorted(forcas)[:3])}")
                    if custo_1k <= 0.001:
                        motivos_detalhes.append("CUSTO ZERO (camada gratuita)")
                    else:
                        motivos_detalhes.append(f"custo_1k≈R${custo_1k:.3f}")
                    if vel_ms:
                        motivos_detalhes.append(f"latencia≈{int(vel_ms)}ms/400tok")
                    # Lista os outros providers disponíveis p/ transparência
                    outros_disp = [
                        p.value for p in ProviderExterno
                        if p != prov_heuristica and len(self._chaves.get(p, "").strip()) > 0
                    ]
                    texto_outros = f"outros disponíveis: {', '.join(outros_disp)}" if outros_disp else "único provider com chave hoje"
                    return DecisaoRoteamento(
                        destino=RoteamentoDestino.API_EXTERNA,
                        motivo=(
                            f"Heurística AUTOMÁTICA (Prometeu decidiu): "
                            f"escolheu {prov_heuristica.value.upper()} para a tarefa "
                            f"(habilidade={habilidade_alvo}). "
                            f"Raciocínio: {' · '.join(motivos_detalhes)}. "
                            f"Balanceamento (sem monopólio) · {texto_outros}. "
                            f"Se discordar, mude o dropdown para 'Ollama Local' ou selecione um provider específico."
                        ),
                        custo_estimado_reais=max(0.005, float(custo_1k) * 2.0),
                        modelo_usar=self._modelos_padrao[prov_heuristica],
                        provedor=prov_heuristica.value,
                    )
            # Não pode usar API OU heurística decidiu LOCAL
            self.total_local += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.LOCAL,
                motivo=(
                    "Heurística AUTOMÁTICA (Prometeu decidiu): tarefa SIMPLES ou API "
                    "indisponível (sem chave / teto R$0). Resposta via Ollama LOCAL = R$ 0,00."
                ),
                modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                provedor="ollama",
            )

        # ==============================================================
        # CASO 3: MODO FORCE LOCAL ATIVO (teto R$ 0,00 OU sem nenhuma chave)
        #   → (fallback para quando nenhum override foi passado)
        # ==============================================================
        if self._modo_force_local and not forcar_api_externa:
            self.total_local += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.LOCAL,
                motivo=(
                    "Modo TEIMOSO: HybridRouter SEMPRE LOCAL "
                    "(PROMETEU_TETO_MENSAL_REAIS <= R$0.00 OU nenhuma chave de API "
                    "configurada em .env)."
                ),
                modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                provedor="ollama",
            )

        # ==============================================================
        # CASO 4: LEGACY forcar_api_externa=True (mantido para compatibilidade)
        # ==============================================================
        if forcar_api_externa:
            if not self._pode_usar_api():
                self.total_local += 1
                return DecisaoRoteamento(
                    destino=RoteamentoDestino.LOCAL,
                    motivo=(
                        "Usuário pediu API externa (FORCE_CLOUD), mas uma das proteções "
                        "ativou: (a) TETO MENSAL R$ estourado, OU (b) NENHUMA chave de API "
                        "configurada em .env. Caiu para LOCAL por segurança."
                    ),
                    modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
                    provedor="ollama",
                )
            provider_escolhido: ProviderExterno = self._escolher_melhor_provider()
            self.total_api_externa += 1
            return DecisaoRoteamento(
                destino=RoteamentoDestino.API_EXTERNA,
                motivo=(
                    f"Usuário forçou API externa explicitamente (FORCE_CLOUD). "
                    f"Fornecedor escolhido = {provider_escolhido.value}. "
                    f"Custo estimado: R$0,03 por chamada. Sempre confirme gasto após uso."
                ),
                custo_estimado_reais=0.03,
                modelo_usar=self._modelos_padrao[provider_escolhido],
                provedor=provider_escolhido.value,
            )

        # ==============================================================
        # CASO 5: Nenhum override cai aqui → PADRÃO (LOCAL)
        # ==============================================================
        self.total_local += 1
        return DecisaoRoteamento(
            destino=RoteamentoDestino.LOCAL,
            motivo="Comportamento padrão do Prometeu: LOCAL primeiro, API externa SÓ por necessidade real.",
            modelo_usar=self.modelo_local_padrao_para(habilidade_alvo),
            provedor="ollama",
        )

    # ------------------------------------------------------------------
    # HEURÍSTICA AUTOMÁTICA INTELIGENTE (usada quando provider = "auto")
    # -------------------------------------------------
    # NÃO MAIS hardcoded "Anthropic primeiro sempre".
    # Regra nova: para TODOS os providers que TEM CHAVE, atribuímos um
    # SCORE PONDERADO por 5 fatores abaixo, combinamos com o tipo de
    # tarefa detectado (codigo_avancado / resposta_simples / texto_grande /
    # arquitetura / geral). Se SCORE >= LIMIAR_MINIMO = 60, consideramos
    # usar API; dentre os que passaram, escolhemos o de MAIOR score.
    # Em caso de EMPATE de score (dentro de ±5 pontos = "praticamente iguais"),
    # usamos ROUND-ROBIN POR CATEGORIA para BALANCEAR o uso entre as APIs
    # (assim não monopoliza Anthropic — usa também Gemini e OpenRouter).
    # ------------------------------------------------------------------
    def _heuristica_automatica_escolhe_provider(
        self, habilidade: str, texto: str
    ) -> Optional[ProviderExterno]:
        import re

        texto_lower = (texto or "").lower()
        if not texto_lower:
            return None

        # -------- 1. Filtros duros: algumas categorias NUNCA saem LOCAL
        if habilidade in ("sistema_operacional", "casa", "audicao", "fonacao", "visual"):
            return None

        # Palavras casuais: só match se for PALAVRA ISOLADA (não substring!)
        # Ex: "xp" não pode casar dentro de "explique". Usamos regex \b word boundary.
        palavras_casual = [
            "oi", "ola", "olá", "e aí", "eaí", "tudo bem", "tudo bom", "boa noite", "bom dia",
            "boa tarde", "prometeu", "jhon", "quem é você", "quem e voce", "qual seu nome",
            "xp", "nível", "nivel", "feito", "marco", "conquista", "wall of wins",
            "como voce esta", "como você está", "valeu", "obrigado", "obrigada",
        ]
        if habilidade == "cortex_geral" and len(texto_lower) < 180:
            for k in palavras_casual:
                # \b garante match de palavra/frase isolada, não substring
                # Compilamos inline (é pequeno, na prática o Python cacheia regex)
                padrao = r"\b" + re.escape(k) + r"\b"
                if re.search(padrao, texto_lower, flags=re.IGNORECASE):
                    return None

        # -------- 2. Detecta CATEGORIA da Tarefa (usado no score + round-robin)
        #    Multi-value flags (podem ser múltiplas ao mesmo tempo)
        kw_codigo_avancado = {
            "rust", "tauri", "tokio", "cargo", "deadlock", "lifetime", "borrow checker",
            "windows api", "win32", "pipe", "stdio", "socket", "tcp", "handshake",
            "langgraph", "orquestrador", "multi-agent", "multi agent", "rag",
            "refatora", "refatorar", "refactoring", "code review", "code-review",
            "design pattern", "padrão de projeto", "padrões de projeto",
            "joins complexos", "serializab", "sqlite wal", "wal mode", "transação",
            "debug complexo", "depurar complexo", "traceback", "stack trace",
        }
        kw_arquitetura_planejamento = {
            "arquitetura", "planejar", "planejamento", "estruturar", "roadmap",
            "especificação", "especificacao", "etapas", "requisitos",
            "como implementar", "como construir", "como fazer um sistema",
            "escala", "escalar", "resiliência", "resiliencia", "fault tolerant",
        }
        kw_analise_grande_texto = {
            "resuma", "resumir", "resumo", "sumarize", "sumarizar",
            "analise o texto", "analisar texto", "analise esse texto",
            "explique esse", "explica esse", "explique o texto", "o que diz o texto",
            "extraia", "extrair", "liste os pontos", "lista os pontos",
            "corrija a redação", "corrigir texto", "revise o texto",
        }
        kw_resposta_simples = {
            "significa", "o que é", "o que eh", "qual a diferença",
            "me explique", "me explique rapidamente", "resposta rapida",
            "resposta rápida", "de forma curta", "breve explicação",
            "1 linha", "uma frase", "sim ou nao", "sim ou não",
            "quanto custa", "qual versão", "versão atual",
        }
        # Conta quantos matches por categoria (0-N)
        def _cnt(s: set[str]) -> int:
            return sum(1 for k in s if k in texto_lower)

        cnt_codigo = _cnt(kw_codigo_avancado) + (1 if habilidade == "codigo" else 0)
        cnt_arq = _cnt(kw_arquitetura_planejamento)
        cnt_grandetexto = _cnt(kw_analise_grande_texto)
        cnt_simples = _cnt(kw_resposta_simples)

        # Se NÃO encontrou palavras-chave de complexidade em nenhuma categoria
        # e o texto é curto → tarefa é leve → LOCAL (padrão segurança poupar custo)
        total_complex = cnt_codigo + cnt_arq + cnt_grandetexto + cnt_simples
        if total_complex <= 0 and habilidade == "cortex_geral" and len(texto_lower) < 300:
            return None

        # Define categoria PRINCIPAL para round-robin
        if cnt_codigo >= cnt_arq and cnt_codigo >= cnt_grandetexto and cnt_codigo >= cnt_simples and cnt_codigo > 0:
            categoria_tarefa = "codigo_avancado"
        elif cnt_arq >= cnt_codigo and cnt_arq >= cnt_grandetexto and cnt_arq >= cnt_simples and cnt_arq > 0:
            categoria_tarefa = "arquitetura_planejamento"
        elif cnt_grandetexto >= cnt_codigo and cnt_grandetexto >= cnt_arq and cnt_grandetexto >= cnt_simples and cnt_grandetexto > 0:
            categoria_tarefa = "analise_grande_texto"
        elif cnt_simples > 0:
            categoria_tarefa = "resposta_simples"
        else:
            categoria_tarefa = "geral"

        # -------- 3. Lista apenas providers que TEM CHAVE configurada hoje
        tem_chave_provider: List[ProviderExterno] = [
            p for p in ProviderExterno if len(self._chaves.get(p, "").strip()) > 0
        ]
        if len(tem_chave_provider) == 0:
            return None

        # -------- 4. Calcula SCORE 0-100 para cada provider disponível
        def _score_para_provider(p: ProviderExterno) -> Tuple[int, Dict[str, int]]:
            perfil = self._perfil_provider[p]
            forcas_provider: set[str] = perfil["forcas"]
            fracos_provider: set[str] = perfil["fraquezas"]

            s_cat = 0
            detalhe_cat = {
                "codigo": 0, "arquitetura": 0, "grandetexto": 0, "simples": 0,
            }
            # Peso por categoria conforme a tarefa
            if cnt_codigo > 0:
                pts = min(40, 10 + 8 * cnt_codigo)  # até 40 pts (aumentado p/ caber bonus fortes)
                if "codigo_avancado" in forcas_provider:
                    pts += 22  # ANTES 12: vantagem CLAARA para providers com raciocinio profundo
                if "raciocinio_logico" in forcas_provider:
                    pts += 15  # ANTES 8: peso maior em código complexo (deadlock, lifetime, etc)
                if "codigo_avancado" in fracos_provider:
                    pts -= 25  # ANTES 15: penalidade maior p/ providers superficiais em código
                detalhe_cat["codigo"] = max(0, pts)
                s_cat += detalhe_cat["codigo"]
            if cnt_arq > 0:
                pts = min(32, 9 + 6 * cnt_arq)
                if "arquitetura_sistema" in forcas_provider or "planejamento_longo_prazo" in forcas_provider:
                    pts += 15  # ANTES 12: peso maior p/ arquitetura e planejamento longo
                detalhe_cat["arquitetura"] = max(0, pts)
                s_cat += detalhe_cat["arquitetura"]
            if cnt_grandetexto > 0:
                pts = min(32, 9 + 5 * cnt_grandetexto)
                if "sumarizacao" in forcas_provider or "texto_grande_analise" in forcas_provider:
                    pts += 14  # ANTES 12
                detalhe_cat["grandetexto"] = max(0, pts)
                s_cat += detalhe_cat["grandetexto"]
            if cnt_simples > 0:
                pts = min(35, 8 + 5 * cnt_simples)  # ANTES min(25, 6+4*) → aumentado p/ passar LIMIAR
                if "resposta_rapida" in forcas_provider or "explicacoes_simple" in forcas_provider:
                    pts += 15  # ANTES 10: reforça resposta rápida em Gemini
                # bonus MASSIVO se custo for 0 (camada gratuita Gemini) p/ respostas simples
                if perfil["custo_nominal_por_1k_tokens_brl"] <= 0.001:
                    pts += 20
                if "respostas_rapidas_curtas" in fracos_provider:
                    pts -= 6  # ANTES 8 (levemente menor p/ não zerar o score do Anthropic em geral)
                detalhe_cat["simples"] = max(0, pts)
                s_cat += detalhe_cat["simples"]

            # ---- PESO CUSTO (0-20 pts inversamente proporcional) ----
            custo = float(perfil["custo_nominal_por_1k_tokens_brl"])
            # Custo 0 = +20 pts. Custo R$0.03 = 0 pts. (linear)
            s_custo = max(0, int(20 - (custo / 0.030) * 20))

            # ---- PESO VELOCIDADE ESPERADA (0-15 pts, maior = melhor) ----
            ms_400 = float(perfil["velocidade_esperada_ms_por_400_out"])
            # 3000ms = +15 pts ; 6000ms = 0 pts (linear desc)
            s_vel = max(0, int(15 - max(0, (ms_400 - 3000)) / 3000 * 15))

            # ---- DIVERSIFICAÇÃO: BÔNUS por "não ter sido usado muito recentemente"
            # Conta quantas chamadas API_EXT foram feitas para cada provider.
            # Se for o MENOS usado, dá +8. Se METADE do líder, dá +4.
            # (garante balanceamento distribuído durante a sessão)
            s_div = 0
            try:
                # Hack: usamos o contador geral da instância; mas na prática o
                # `total_api_externa` é global. Para SCORE por provider, um
                # proxy justo: contar quantas vezes cada provider apareceu nas
                # últimas `decisoes` seria melhor. Mas o singleton já separa
                # no `hybrid_router._cnt_uso_provider` se existir. Se não,
                # pulamos.
                cnts: Dict[str, int] = getattr(self, "_cnt_uso_por_provider", {}) or {}
                if cnts:
                    vals = list(cnts.values())
                    menor = min(vals)
                    maior = max(vals)
                    meu_cnt = cnts.get(p.value, 0)
                    if maior > menor and meu_cnt == menor:
                        s_div = 8
                    elif maior - meu_cnt >= 3:
                        s_div = 4
            except Exception:
                pass

            score_total = max(0, min(100, s_cat + s_custo + s_vel + s_div))
            return score_total, {
                "categoria": s_cat,
                "custo": s_custo,
                "velocidade": s_vel,
                "diversificacao": s_div,
            }

        scored: List[Tuple[ProviderExterno, int, Dict[str, int]]] = []
        for p in tem_chave_provider:
            score, detalhe = _score_para_provider(p)
            scored.append((p, score, detalhe))

        # Só considera providers com score >= LIMIAR_MINIMO = 55.
        # (abaixo disso = "não vale gastar API, cai local")
        # Era 60 → 55 para respostas curtas/simples passarem com margem.
        LIMIAR = 55
        aptos: List[Tuple[ProviderExterno, int, Dict[str, int]]] = [
            s for s in scored if s[1] >= LIMIAR
        ]
        if len(aptos) == 0:
            return None

        # Ordena DO MAIOR SCORE para o menor.
        aptos.sort(key=lambda item: item[1], reverse=True)
        melhor_score = aptos[0][1]

        # -------- 5. ROUND-ROBIN POR CATEGORIA: pega TODOS os providers que
        # estão dentro de ±4 pontos do melhor (empate estatístico) e escolhe
        # por rotação da categoria tarefa.
        # (±5 → ±4 para evitar "falsos empates" quando há diferença real de performance)
        # Isso resolve o problema do Jhon: "ele só escolhia Anthropic".
        # Agora se Anthropic=92, Gemini=90 → empatados, alterna 1 por 1.
        margem_empate = 4
        empatados = [a for a in aptos if (melhor_score - a[1]) <= margem_empate]
        if len(empatados) >= 2:
            idx_rodada = self._rr_por_categoria.get(categoria_tarefa, 0) % len(empatados)
            self._rr_por_categoria[categoria_tarefa] = idx_rodada + 1
            escolhido = empatados[idx_rodada][0]
        else:
            escolhido = aptos[0][0]

        # Registra uso p/ pontuação de diversificação nas próximas
        self._cnt_uso_por_provider: Dict[str, int] = getattr(
            self, "_cnt_uso_por_provider", {}
        ) or {}
        self._cnt_uso_por_provider[escolhido.value] = (
            self._cnt_uso_por_provider.get(escolhido.value, 0) + 1
        )

        # Loga a decisão COMPLETA (ajuda debug e transparência futura)
        try:
            detalhes_log = [
                f"cat={categoria_tarefa}",
                f"cnt(cod/arq/gtx/sim)={cnt_codigo}|{cnt_arq}|{cnt_grandetexto}|{cnt_simples}",
                *[
                    f"{p.value}={s}pts {d}"
                    for (p, s, d) in scored
                ],
            ]
            log.info(
                "hybrid_heuristica_automatica",
                {
                    "categoria_tarefa": categoria_tarefa,
                    "escolhido": escolhido.value,
                    "score_escolhido": next(iter([s for p, s, _ in scored if p == escolhido]), 0),
                    "providers_avaliados": detalhes_log,
                    "habilidade": habilidade,
                },
            )
        except Exception:
            pass

        return escolhido

    # ------------------------------------------------------------------
    # Helpers publicos
    # ------------------------------------------------------------------
    def modelo_local_padrao_para(self, habilidade: str) -> str:
        """Diz qual modelo local usar p/ cada habilidade."""
        if habilidade == "codigo":
            # Qwen Coder é melhor, mas se não existir no Ollama ainda, cai no Llama 3.
            return "qwen2.5-coder:7b"
        return "llama3.1:8b"                # padrão geral conversa

    def providers_disponiveis(self) -> List[Tuple[str, bool]]:
        """Retorna lista (nome_provider, tem_chave_configurada?) para UI mostrar."""
        return [(p.value, bool(self._chaves[p])) for p in ProviderExterno]

    # ------------------------------------------------------------------
    # Helpers privados (nunca chamar fora da classe)
    # ------------------------------------------------------------------
    def _n_tem_nenhuma_chave(self) -> bool:
        """True = nenhum provider externo tem chave preenchida."""
        return all(len(chave.strip()) == 0 for chave in self._chaves.values())

    def _escolher_melhor_provider(self) -> ProviderExterno:
        """
        Ordem de preferência: OpenRouter > Anthropic direto > Gemini.
        Garante SEMPRE retorna um provider que TEM CHAVE (chamador já validou).
        """
        for provider in ProviderExterno:
            if len(self._chaves[provider].strip()) > 0:
                return provider
        # Fallback: não deveria chegar aqui pois _pode_usar_api já valida,
        # mas retorna OPENROUTER por segurança (nunca vai ser usado).
        return ProviderExterno.OPENROUTER

    def _pode_usar_api(self) -> bool:
        """
        True = (tem pelo MENOS 1 chave em algum provider)
            AND (ainda não estourou teto do mês)
            AND (teto_mensal_reais > 0.0)
        """
        if self._n_tem_nenhuma_chave():
            return False
        if self.teto_mensal_reais <= 0.0:
            return False
        return self.custo_acumulado_reais_mes < self.teto_mensal_reais

    def _estado_dict(self) -> Dict[str, Any]:
        return {
            "modo_force_local": self._modo_force_local,
            "providers_configurados": {
                p.value: len(self._chaves[p].strip()) > 0 for p in ProviderExterno
            },
            "teto_mensal_reais": self.teto_mensal_reais,
            "gasto_atual_mes_reais": round(self.custo_acumulado_reais_mes, 2),
            "pode_usar_api": self._pode_usar_api(),
        }


# Singleton global
hybrid_router: HybridRouter = HybridRouter()
