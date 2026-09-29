"use client";

// ================================================================
// PAGINA /especialistas · GRID 7 CARTES
// IDs BATEM VERBATIM core/progress_rpg.py:33-41 TipoHabilidade
// ================================================================

import React, { useMemo, useState } from "react";
import { usePainelStatus, API_BASE } from "../../components/use_painel_status";
import { useTauriEnv } from "../../components/use_tauri_env";
import { Card, CirculoStatus, BarraProgresso } from "../../components/ui_utils";

type IdHab = "cortex_geral" | "codigo" | "audicao" | "fonacao" | "sistema_operacional" | "visual" | "casa";

type CardHab = {
  id: IdHab;
  nome: string;
  icone: string;
  regiao: string;
  fase: number;
  descricao: string;
  cor: string;
  is_loaded: boolean;
  modelo: string;
  pingPrompt: string;
};

const HAB_BASE: CardHab[] = [
  { id: "cortex_geral",       nome: "Córtex Geral",       icone: "🧠", regiao: "llm_core",       fase: 1, is_loaded: true,  modelo: "llama3:latest",         cor: "#F59E0B", descricao: "Região raciocínio geral. Roteamento default.", pingPrompt: "Oi, quem é você? Responda em 1 frase curta." },
  { id: "codigo",            nome: "Código",             icone: "⚡", regiao: "llm_code",       fase: 2, is_loaded: true,  modelo: "deepseek-coder:6.7b-instruct-q4_K_M", cor: "#3B82F6", descricao: "Refatora, documenta, escreve código.", pingPrompt: "Crie uma função JS curta: soma de 2 números. Apenas o código." },
  { id: "audicao",           nome: "Audição",           icone: "👂", regiao: "stt_whisper",    fase: 3, is_loaded: false, modelo: "openai/whisper-small",   cor: "#8B5CF6", descricao: "Audio → texto (a implementar).", pingPrompt: "[audicao] STT: a implementar." },
  { id: "fonacao",           nome: "Fonação",           icone: "🗣️", regiao: "tts_xtts",       fase: 3, is_loaded: false, modelo: "coqui/xtts",            cor: "#EC4899", descricao: "Texto → audio (a implementar).", pingPrompt: "[fonacao] TTS: a implementar." },
  { id: "sistema_operacional",nome: "Sistema Operacional",  icone: "🖥️", regiao: "os_control",   fase: 2, is_loaded: true,  modelo: "whitelist CMD",           cor: "#10B981", descricao: "Abre programas, listar pastas permitidas.", pingPrompt: "abre a calculadora." },
  { id: "visual",            nome: "Visual",              icone: "👁️", regiao: "image_flux",     fase: 5, is_loaded: false, modelo: "black-forest-labs/flux", cor: "#F97316", descricao: "Geração de imagens (a implementar).", pingPrompt: "[visual] flux: a implementar." },
  { id: "casa",              nome: "Casa Inteligente",  icone: "🏠", regiao: "home_control",   fase: 4, is_loaded: false, modelo: "MQTT/Philips Hue",       cor: "#06B6D4", descricao: "Controlar luzes e sensores (a implementar).", pingPrompt: "[casa] home: a implementar." },
];

export default function EspecialistasPage() {
  const ps = usePainelStatus(4000);
  const tauri = useTauriEnv();
  const [busy, setBusy] = useState<IdHab | null>(null);
  const [lastResp, setLastResp] = useState<Partial<Record<IdHab, string>>>({});

  const habsComXP = useMemo(() => {
    const arr = ps.painel?.rpg?.habilidades?.length ? ps.painel.rpg.habilidades : [];
    return HAB_BASE.map((hb) => {
      const ui = arr.find((x) => x.id === hb.id);
      return {
        ...hb,
        nivel: ui?.nivel ?? 0,
        xp: ui?.xp ?? 0,
        xp_para_prox: ui?.xp_para_prox ?? 100,
        is_loaded: hb.is_loaded || !!ui?.ativo || (ui?.nivel ?? 0) > 0,
      };
    });
  }, [ps.painel]);

  async function testarRapido(id: IdHab) {
    if (busy) return;
    const cfg = HAB_BASE.find((x) => x.id === id)!;
    setBusy(id);
    setLastResp((r) => ({ ...r, [id]: "⟳ Enviando…" }));
    try {
      const r = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: cfg.pingPrompt, habilidade_alvo: id })
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json();
      setLastResp((rr) => ({ ...rr, [id]: String(j.resposta_texto ?? "ok").slice(0, 220) + (String(j.resposta_texto ?? "").length > 220 ? "…" : "") }));
      setTimeout(() => ps.carregar(true), 250);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "erro";
      setLastResp((rr) => ({ ...rr, [id]: "⚠️ " + msg }));
    } finally {
      setTimeout(() => setBusy(null), 300);
    }
  }

  return (
    <div className="h-full w-full overflow-y-auto px-6 py-5 space-y-5">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-[20px] font-bold flex items-center gap-2">
            🧬 7 Especialistas · Regiões Cerebrais
          </h1>
          <p className="text-[12px] text-muted mt-0.5 max-w-3xl">
            Cada cartão abaixo corresponde 1:1 ao enum <code className="px-1 bg-bg2 rounded border border-border1 mx-1 font-mono text-[11px]">TipoHabilidade</code> em{" "}
            <code className="font-mono text-[11px]">core/progress_rpg.py</code>.
            Botão <b>Testar Rápido</b> envia um prompt ping via <code>/api/chat</code> com <code>habilidade_alvo</code> direto.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[12px]">
          <span className="text-muted">{habsComXP.filter(h => h.is_loaded).length}/7 carregados</span>
          <span className="h-6 px-2 rounded-md bg-bg2 border border-border1 text-muted grid place-items-center">
            R$ 0,00 · Local
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
        {habsComXP.map((h) => (
          <Card
            key={h.id}
            icon={h.icone}
            title={h.nome}
            right={
              <span className="flex items-center gap-1.5 text-[11px]">
                <CirculoStatus online={h.is_loaded} />
                <span className={h.is_loaded ? "text-success" : "text-muted"}>
                  {h.is_loaded ? "Carregado" : "Esqueleto"}
                </span>
              </span>
            }
            className="flex flex-col h-full"
          >
            <div className="flex items-center justify-between mt-2">
              <div className="rounded-full px-2 py-0.5 text-[10px] font-mono font-bold border"
                style={{ borderColor: h.cor + "55", color: h.cor, backgroundColor: h.cor + "14" }}>
                {h.regiao}
              </div>
              <div className="text-[10.5px] text-muted font-mono">
                fase {h.fase}/5
              </div>
            </div>

            <p className="text-[12px] text-muted mt-2 min-h-[48px] leading-snug">
              {h.descricao}
            </p>

            <div className="mt-1 text-[11px] text-muted">
              <div className="flex items-center justify-between mb-1">
                <span>Modelo:</span>
                <span className="text-foreground font-mono truncate max-w-[60%]" title={h.modelo}>{h.modelo}</span>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span>XP:</span>
                <span className="text-foreground font-mono">
                  LVL {h.nivel} · {h.xp}/{h.xp_para_prox}
                </span>
              </div>
              <BarraProgresso xp={h.xp} xpProx={h.xp_para_prox} cor={h.cor} />
            </div>

            <div className="mt-3 pt-3 border-t border-border1">
              <button
                onClick={() => testarRapido(h.id)}
                disabled={busy === h.id || !h.is_loaded}
                className={"h-9 w-full rounded-md text-[12px] font-semibold transition border disabled:opacity-50 disabled:cursor-not-allowed" +
                  (h.is_loaded
                    ? " bg-bg3 border-border1 hover:bg-accent hover:text-bg0 hover:border-accent"
                    : " bg-bg2 border-dashed border-border1 text-muted cursor-not-allowed")}
              >
                {busy === h.id ? "⟳ Testando…" : h.is_loaded ? "▶ Testar Rápido" : "⏸ A Implementar"}
              </button>
              {lastResp[h.id] && (
                <div className="mt-2 rounded-md bg-bg2 border border-border1 p-2 text-[11.5px] leading-relaxed whitespace-pre-wrap break-words max-h-28 overflow-y-auto">
                  {lastResp[h.id]}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
