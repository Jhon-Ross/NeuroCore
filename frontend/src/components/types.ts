"use client";

import { useEffect, useState } from "react";

// ================================================================
// TIPOS COMPARTILHADOS ENTRE PÁGINAS DO LAUNCHER
// Alinhados com core/api.py Pydantic
// ================================================================

export function useIsMounted(): boolean {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}

export type HabilidadeUI = {
  id: string;
  nome: string;
  nivel: number;
  xp: number;
  xp_para_prox: number;
  icone: string;
  ativo?: boolean;
  regiao: string;
  fase: string;
};

export type FeitoUI = {
  id: number;
  nome: string;
  data: string;
  emoji: string;
  descricao: string;
};

export type PainelStatus = {
  timestamp_unix: number;
  uptime_segundos: number;
  rpg: {
    nivel_global: number;
    xp_total: number;
    xp_para_proximo_nivel: number;
    habilidades: HabilidadeUI[];
    feitos: FeitoUI[];
  };
  vram: { online: boolean; total_gb: number; resumo: string };
  router: {
    modo_force_local: boolean;
    providers_configurados?: Record<string, boolean>;
    teto_mensal_reais: number;
    gasto_atual_mes_reais?: number;
    pode_usar_api?: boolean;
  };
  especialistas: Record<
    string,
    { fase: number; is_loaded: boolean; modelo?: string }
  >;
  // NOVO: Lista de providers para o dropdown do chat, já vem calculada do backend
  // (inclui `disponivel: boolean` e `motivo_indisponivel` caso não tenha chave/teto=0)
  providers_disponiveis?: ProviderOpcaoUI[];
};

// -------- Tipos de PROVIDER (Dropdown Seleção de Inferência) --------

/** Valores válidos para o campo `provider` do request POST /api/chat.
 *  Deve bater exatamente com core.api._PROVIDERS_VALIDOS. */
export type ProviderValor = "auto" | "local" | "openrouter" | "anthropic" | "gemini";

/** Estrutura de 1 item da lista `providers_disponiveis` que vem de GET /api/status.
 *  O backend já calcula `disponivel` pra gente (se tem chave + teto > 0).
 *  `undefined` = ainda não sabemos (fallback offline enquanto a API :8000 não deu a primeira resposta). */
export type ProviderOpcaoUI = {
  valor: ProviderValor;
  label: string;
  descricao: string;
  custo_nominal_brl: number;
  requer_chave: boolean;
  env_var?: string;
  disponivel: boolean | undefined;
  motivo_indisponivel?: string;
};

// -------- Tipos adicionais do Launcher --------

export type ServicoNome = "ollama" | "api" | "frontend" | "chatcli";

export type StatusServico = {
  nome: ServicoNome;
  rotulo: string;
  icone: string;
  online: boolean;
  pid?: number;
  porta?: number;
  uptime_segundos?: number;
  memoria_mb?: number;
};

export type SparkSeries = {
  cpu: number[];
  ram: number[];
  vram: number[];
  latencia_ms: number[];
};

export type LauncherConfig = {
  abrir_chat_em_webview: boolean;
  manter_ollama_vivo_ao_sair: boolean;
  poll_interval_ms: number;
  tema: "preto_ambar";
};

// -------- Tipos de Chat --------
export type MensagemChat = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  tempo_ms?: number;
  modelo?: string;
  tokens?: number;
  xp?: number;
  // NOVOS CAMPOS PROVIDER — preenchidos quando a resposta vem via API externa
  provedor?: string;              // ex: "ollama", "anthropic", "openrouter", "gemini"
  roteamento_motivo?: string;     // texto explicando o porquê da escolha (ex: "Usuário selecionou Anthropic")
  custo_estimado_reais?: number;  // ex: 0.03 = R$ 0,03
};
