"use client";

import { useEffect, useState } from "react";
import { useTauriEnv } from "./use_tauri_env";
import type { PainelStatus, HabilidadeUI, FeitoUI, StatusServico, ServicoNome } from "./types";

export const API_BASE = "http://127.0.0.1:8000";

// ================================================================
// HOOK: Busca GET /api/status com polling e fallback offline amigavel
// 🔁 Desktop Tauri (isTauri=true): DESVIO DE CORS
//   - Primeiro invoke("check_services") Rust (reqwest nativo, sem CORS)
//     para saber se serviços estão de pé (Ollama / API / Frontend).
//   - Depois fetch /api/status para RPG/XP/Habilidades (agora CORS=*)
// 🌐 Navegador Preview (isTauri=false):
//   - Apenas fetch /api/status HTTP
// ================================================================

const HABILIDADES_FALLBACK: HabilidadeUI[] = [
  { id: "cortex_geral", nome: "Córtex Geral", nivel: 1, xp: 0, xp_para_prox: 100, icone: "🧠", ativo: true, regiao: "llm_core", fase: "1/5" },
  { id: "codigo", nome: "Código", nivel: 0, xp: 0, xp_para_prox: 100, icone: "⚡", regiao: "llm_code", fase: "2/5" },
  { id: "audicao", nome: "Audição", nivel: 0, xp: 0, xp_para_prox: 100, icone: "👂", regiao: "stt_whisper", fase: "3/5" },
  { id: "fonacao", nome: "Fonação", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🗣️", regiao: "tts_xtts", fase: "3/5" },
  { id: "sistema_operacional", nome: "S.O.", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🖥️", regiao: "os_control", fase: "2/5" },
  { id: "visual", nome: "Visual", nivel: 0, xp: 0, xp_para_prox: 100, icone: "👁️", regiao: "image_flux", fase: "5/5" },
  { id: "casa", nome: "Casa Inteligente", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🏠", regiao: "home_control", fase: "4/5" },
];

const FEITOS_FALLBACK: FeitoUI[] = [
  { id: 1, nome: "Marco 0 · Nascimento", data: "27/09/2026", emoji: "🌱", descricao: "Arquitetura NeuroCore aprovada." },
  { id: 2, nome: "Marco 1 · Primeira Palavra", data: "28/09/2026", emoji: "💬", descricao: "Primeira resposta: llama3:latest · 409tok · 526ms." },
];

export function usePainelStatus(intervalMs = 4000) {
  const tauri = useTauriEnv();
  const [painel, setPainel] = useState<PainelStatus | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [latenciaUltimaMs, setLatenciaUltimaMs] = useState<number | null>(null);
  const [tentativasFalhas, setTentativasFalhas] = useState(0);
  const [servicosRust, setServicosRust] = useState<Record<string, StatusServico> | null>(null);
  const [primeiraSondaEm, setPrimeiraSondaEm] = useState<number | null>(null);

  async function carregar(silencioso = false) {
    const t0 = performance.now();
    setPrimeiraSondaEm((t) => (t === null ? Date.now() : t));

    // ------------------- ETAPA 1: RUST (TAURI, sem CORS) -------------------
    let statusServicos: Record<string, StatusServico> | null = null;
    if (tauri.ready && tauri.isTauri) {
      try {
        const res = await tauri.invoke<Array<StatusServico & { nome: ServicoNome }>>("check_services");
        const acc: Record<string, StatusServico> = {};
        for (const s of res) {
          const nome = (s as any).nome as ServicoNome;
          if (nome) acc[String(nome)] = s;
        }
        statusServicos = acc;
        setServicosRust(acc);
      } catch {
        statusServicos = null;
      }
    }

    const apiOnRust = !!statusServicos && (
      !!statusServicos["Api"]?.online ||
      !!statusServicos["api"]?.online ||
      !!statusServicos["FastAPI"]?.online
    );

    // ------------------- ETAPA 2: HTTP fetch /api/status -------------------
    try {
      const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
      const t = ctrl ? setTimeout(() => ctrl!.abort(), 6000) : null;
      const r = await fetch(`${API_BASE}/api/status`, {
        cache: "no-store",
        signal: ctrl?.signal ?? undefined,
      });
      if (t) clearTimeout(t);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j: PainelStatus = await r.json();
      setPainel(j);
      if (!silencioso) setErro(null);
      setTentativasFalhas(0);
      setLatenciaUltimaMs(Math.max(0, Math.round(performance.now() - t0)));
    } catch (e) {
      const msg = e instanceof Error
        ? (e.name === "AbortError" ? "Sonda :8000 timeout após 6s" : e.message)
        : "Falha ao buscar status";
      if (!silencioso && !apiOnRust) {
        if (tentativasFalhas + 1 >= 2) setErro(msg);
      } else if (!silencioso && apiOnRust) {
        setErro(null);
      }
      setTentativasFalhas((x) => x + 1);
      setLatenciaUltimaMs(null);
    }
  }

  useEffect(() => {
    carregar(false);
    const t = window.setInterval(() => carregar(true), intervalMs);
    return () => window.clearInterval(t);
  }, [intervalMs, tauri.ready, tauri.isTauri]);

  const habilidades: HabilidadeUI[] = (() => {
    const arr = painel?.rpg?.habilidades?.length
      ? painel.rpg.habilidades
      : HABILIDADES_FALLBACK;
    return arr.map((h, idx) => ({
      ...h,
      ativo: idx === 0 ? true : (h.ativo ?? (h.nivel > 0 || h.xp > 0)),
    }));
  })();

  const feitos: FeitoUI[] =
    painel?.rpg?.feitos?.length ? painel.rpg.feitos : FEITOS_FALLBACK;
  const xpTotal = habilidades.reduce((a, b) => a + (b.xp || 0), 0);
  const nivelGlobal = painel?.rpg?.nivel_global ?? 1;
  const xpParaProx =
    painel?.rpg?.xp_para_proximo_nivel ?? (nivelGlobal + 1) * 100;

  const apiOnline = (() => {
    const rustOn = !!servicosRust && (
      !!servicosRust["Api"]?.online ||
      !!servicosRust["api"]?.online ||
      !!servicosRust["FastAPI"]?.online
    );
    if (rustOn) return true;
    if (painel) return true;
    if (tentativasFalhas >= 2) return false;
    // Término do período "sondando": após 18s desde a primeira sonda e pelo
    // menos 1 falha, declara OFFLINE. Não permite verde falso permanente.
    if (
      typeof primeiraSondaEm === "number" &&
      Date.now() - primeiraSondaEm > 18_000 &&
      tentativasFalhas >= 1
    ) {
      return false;
    }
    return null;
  })();

  return {
    painel,
    erro,
    latenciaUltimaMs,
    tentativasFalhas,
    habilidades,
    feitos,
    xpTotal,
    nivelGlobal,
    xpParaProx,
    carregar,
    servicosRust,
    apiOnline,
  };
}
