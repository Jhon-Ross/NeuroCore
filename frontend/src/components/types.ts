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
    openrouter_key_configurada: boolean;
    teto_mensal_reais: number;
  };
  especialistas: Record<
    string,
    { fase: number; is_loaded: boolean; modelo?: string }
  >;
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
};
