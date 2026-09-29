"use client";

import React from "react";

// ================================================================
// DIA 1 — ESQUELETO LAYOUT 3 COLUNAS
//   Sidebar 240px  |  Chat Central (flex)  |  Painel RPG 320px
// Design System: PRETO #07070A bg0 + ÂMBAR #F59E0B accent
// ================================================================
// Valores mockados (placeholder) — equivalem ao resumo_para_ui() do
// core/progress_rpg.py. Depois este componente vai ler /api/status
// via fetch do FastAPI.
// ================================================================

const HABILIDADES_PLACEHOLDER = [
  { id: "cortex_geral",  nome: "Córtex Geral",    nivel: 1, xp: 121, xp_para_prox: 100, icone: "🧠", ativo: true,
    regiao: "llm_core", fase: "1/5" },
  { id: "codigo",       nome: "Código",          nivel: 0, xp:   0, xp_para_prox: 100, icone: "⚡", ativo: false,
    regiao: "llm_code", fase: "2/5" },
  { id: "audicao",      nome: "Audição",         nivel: 0, xp:   0, xp_para_prox: 100, icone: "👂", ativo: false,
    regiao: "stt_whisper", fase: "3/5" },
  { id: "fonacao",      nome: "Fonação",         nivel: 0, xp:   0, xp_para_prox: 100, icone: "🗣️", ativo: false,
    regiao: "tts_xtts", fase: "3/5" },
  { id: "sistema_operacional", nome: "S.O.",     nivel: 0, xp:   0, xp_para_prox: 100, icone: "🖥️", ativo: false,
    regiao: "os_control", fase: "2/5" },
  { id: "visual",       nome: "Visual",          nivel: 0, xp:   0, xp_para_prox: 100, icone: "👁️", ativo: false,
    regiao: "image_flux", fase: "5/5" },
  { id: "casa",         nome: "Casa Inteligente",nivel: 0, xp:   0, xp_para_prox: 100, icone: "🏠", ativo: false,
    regiao: "home_control", fase: "4/5" },
] as const;

const FEITOS_PLACEHOLDER = [
  { id: 0, nome: "Marco 0 · Nascimento",  data: "27/09/2026", emoji: "🌱",
    descricao: "Arquitetura NeuroCore aprovada, RPG anti-abandono desenhado." },
  { id: 2, nome: "Marco 2 · Primeira Palavra", data: "28/09/2026", emoji: "💬",
    descricao: "Prometeu respondeu sua primeira pergunta: llama3:latest · 409tok · 526ms." },
] as const;

// Seed determinística (evita warning hidratação server/client)
function _seedFake(len = 60, seed = 42): number[] {
  let s = seed;
  const out: number[] = [];
  for (let i = 0; i < len; i++) {
    s = (s * 9301 + 49297) % 233280;
    const rnd = s / 233280;
    out.push(30 + rnd * 70);
  }
  return out;
}
const SPARK_FAKE = _seedFake(60, 1337);

function Sparkline({ data, cor }: { data: number[]; cor: string }) {
  const w = 200;
  const h = 36;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const pontos = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / Math.max(1, max - min)) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible">
      <polyline fill="none" stroke={cor} strokeWidth="1.5" points={pontos} />
    </svg>
  );
}

function BarraProgresso({ xp, xpProx }: { xp: number; xpProx: number }) {
  const pct = Math.min(100, Math.round((xp / Math.max(1, xpProx)) * 100));
  return (
    <div className="h-1.5 w-full rounded-full bg-bg3 overflow-hidden">
      <div
        className="h-full rounded-full transition-[width] duration-700"
        style={{ width: `${pct}%`,
                 background: "linear-gradient(90deg,#F59E0B 0%,#FBBF24 100%)" }}
      />
    </div>
  );
}

export default function Home() {
  const xpGlobalTotal = HABILIDADES_PLACEHOLDER.reduce((a, b) => a + b.xp, 0);
  const nivelGlobal = 1;
  const xpProxNivel = (nivelGlobal + 1) * 100;
  const xpFaltante = xpProxNivel - xpGlobalTotal;

  return (
    <div className="h-screen w-screen max-h-screen max-w-screen overflow-hidden bg-bg0 text-foreground font-sans text-sm">
      <div className="h-full w-full grid"
           style={{ gridTemplateColumns: "240px 1fr 320px", gap: "0px" }}>

        {/* ============================================================
             COLUNA 1 · SIDEBAR ESQUERDA 240px
             ============================================================ */}
        <aside className="h-full w-full bg-bg1 border-r border-border1 flex flex-col">
          {/* Logo Prometeu */}
          <div className="h-14 px-4 flex items-center gap-3 border-b border-border1">
            <div className="h-8 w-8 rounded-full grid place-items-center bg-accent text-bg0 font-bold select-none">
              P
            </div>
            <div className="leading-tight">
              <div className="text-[15px] font-bold text-accent">Prometeu</div>
              <div className="text-[11px] text-muted -mt-0.5">NeuroCore · Fase Embrião</div>
            </div>
          </div>

          {/* Navegação */}
          <nav className="px-2 py-3 flex flex-col gap-1">
            {[
              { nome: "Chat",     ativo: true,  ico: "💬" },
              { nome: "Histórico",ativo: false, ico: "📚" },
              { nome: "Rituais",  ativo: false, ico: "🌿" },
              { nome: "Memória",  ativo: false, ico: "🧠" },
              { nome: "Config.",  ativo: false, ico: "⚙️" },
            ].map((m) => (
              <button
                key={m.nome}
                className={`h-9 w-full px-3 rounded-md flex items-center gap-3 transition
                  ${m.ativo
                    ? "bg-bg3 text-foreground border border-border1"
                    : "text-muted hover:bg-bg2 hover:text-foreground border border-transparent"}`}
              >
                <span className="text-base">{m.ico}</span>
                <span className="text-[13px] font-medium">{m.nome}</span>
              </button>
            ))}
          </nav>

          <div className="h-px bg-border1 mx-3 my-1" />

          {/* Sessões recentes */}
          <div className="px-4 pt-3 pb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Sessões</span>
            <button className="text-accent hover:underline text-[11px] font-bold">+ nova</button>
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
            {[
              { nome: "Primeira Palavra",  data: "28/09 23:30", msgs:  8, ativo: true  },
              { nome: "Planejamento Dia 0",data: "27/09 19:12", msgs: 42, ativo: false },
              { nome: "Wall of Wins",      data: "27/09 18:41", msgs: 13, ativo: false },
              { nome: "Teste Ollama AMD",  data: "27/09 15:02", msgs:  4, ativo: false },
            ].map((s) => (
              <div key={s.nome}
                   className={`h-14 w-full rounded-md px-3 flex flex-col justify-center cursor-pointer transition
                     ${s.ativo ? "bg-bg3 border border-border1" : "hover:bg-bg2 border border-transparent"}`}>
                <div className="flex items-center justify-between">
                  <div className="truncate text-[13px] font-medium">{s.nome}</div>
                  <div className="text-[10px] text-muted ml-2 shrink-0">{s.data}</div>
                </div>
                <div className="text-[11px] text-muted">{s.msgs} mensagens</div>
              </div>
            ))}
          </div>
        </aside>

        {/* ============================================================
             COLUNA 2 · CHAT CENTRAL (flex 1fr)
             ============================================================ */}
        <main className="h-full w-full flex flex-col bg-bg0">
          {/* Barra de topo do chat */}
          <div className="h-14 px-6 flex items-center justify-between border-b border-border1 bg-bg1/40 backdrop-blur">
            <div>
              <div className="text-[15px] font-bold">Primeira Palavra — Sessão 10</div>
              <div className="text-[11px] text-muted -mt-0.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-success mr-1.5 align-middle" />
                Córtex Geral · llama3:latest · RX 7600 8GB · Local 100%
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-8 px-3 rounded-md bg-bg2 border border-border1 text-[11px] text-muted grid place-items-center">
                Modelo: <span className="text-foreground ml-1 font-mono">llama3:latest</span>
              </div>
              <div className="h-8 px-3 rounded-md bg-accent-soft border border-accent/40 text-[11px] text-accent grid place-items-center font-semibold">
                Hybrid Router · FORCE LOCAL
              </div>
            </div>
          </div>

          {/* Área de mensagens — VAZIA DIA 1 (espera FastAPI) */}
          <div className="flex-1 overflow-y-auto px-14 py-10 flex flex-col justify-end gap-6">
            <div className="mx-auto max-w-3xl w-full rounded-xl border border-border1 bg-bg1 px-8 py-10 text-center shadow-glow">
              <div className="text-5xl mb-3">🧠✨</div>
              <div className="text-[20px] font-bold text-accent mb-2">
                Prometeu está acordando, Jhon!
              </div>
              <div className="text-muted text-[13px] max-w-xl mx-auto leading-relaxed">
                Área do chat — Dia 1. Aqui vão aparecer as mensagens trocadas com Prometeu.
                Por enquanto, experimente o{" "}
                <code className="bg-bg3 text-accent px-1.5 py-0.5 rounded font-mono text-[12px]">
                  scripts\iniciar_prometeu.ps1
                </code>{" "}
                para o chat em CLI já funcional. Amanhã (Dia 2) a FastAPI conecta este painel ao cérebro.
              </div>
              <div className="mt-6 flex flex-wrap justify-center gap-2 text-[11px]">
                {["Fase Embrião · 7 regiões cerebrais",
                  "LangGraph · SQLite ACID",
                  "Ollama · DirectML · AMD RX 7600",
                  "XP por interação · Wall of Wins",
                 ].map((t) => (
                  <span key={t} className="px-3 py-1 rounded-full bg-bg3 border border-border1 text-muted">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Caixa de input — placeholder (Dia 2 conecta no /api/chat) */}
          <div className="h-28 px-14 pb-6 pt-4 border-t border-border1 bg-bg1/40">
            <div className="mx-auto max-w-3xl w-full h-full grid grid-cols-[1fr_auto] gap-3">
              <textarea
                placeholder="Digite algo para o Prometeu… (Dia 2: aqui conecta na FastAPI /api/chat)"
                disabled
                className="h-full w-full resize-none rounded-xl bg-bg2 border border-border1 px-4 py-3
                           text-[13px] text-muted placeholder:text-muted/60 outline-none focus:ring-1 focus:ring-accent/50"
              />
              <button
                disabled
                className="h-full px-5 rounded-xl bg-accent text-bg0 font-bold text-[13px]
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ↵ Enviar
              </button>
            </div>
          </div>
        </main>

        {/* ============================================================
             COLUNA 3 · PAINEL DIREITO RPG + STATUS 320px
             ============================================================ */}
        <aside className="h-full w-full bg-bg1 border-l border-border1 flex flex-col">
          {/* Nível Global */}
          <div className="h-36 px-5 py-4 border-b border-border1 bg-gradient-to-b from-bg2 to-bg1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                Nível Global
              </span>
              <span className="h-6 px-2 rounded-md bg-accent-soft border border-accent/40 text-accent
                               text-[11px] font-bold grid place-items-center">
                LVL {nivelGlobal}
              </span>
            </div>
            <div className="flex items-end justify-between mb-2">
              <div className="leading-none">
                <div className="text-[28px] font-bold tracking-tight">
                  {xpGlobalTotal}
                  <span className="text-muted text-[13px] font-normal ml-1"> XP</span>
                </div>
                <div className="text-[11px] text-muted mt-1">
                  Falta <span className="text-accent font-semibold">{xpFaltante} XP</span> para LVL {nivelGlobal + 1}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-muted mb-0.5">Feitos</div>
                <div className="text-[22px] font-bold text-accent leading-none">
                  {FEITOS_PLACEHOLDER.length}
                </div>
              </div>
            </div>
            <BarraProgresso xp={xpGlobalTotal} xpProx={xpProxNivel} />
          </div>

          {/* 7 Habilidades / Regiões Cerebrais */}
          <div className="px-5 pt-3 pb-1 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              7 Habilidades · Regiões
            </span>
            <span className="text-[10px] text-muted">Fase N/5</span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
            {HABILIDADES_PLACEHOLDER.map((h) => (
              <div key={h.id}
                   className={`rounded-lg px-3 py-2 border transition
                     ${h.ativo
                        ? "bg-bg2 border-accent/30 shadow-[0_0_0_1px_#F59E0B22]"
                        : "bg-bg1/50 border-border1 opacity-80"}`}>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[14px]">{h.icone}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="truncate text-[12.5px] font-semibold">
                        {h.nome}
                        {h.ativo && (
                          <span className="ml-1.5 text-[9px] font-bold uppercase tracking-wider text-success">
                            ● ativa
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-muted font-mono shrink-0">
                        LVL {h.nivel} · f{h.fase}
                      </div>
                    </div>
                    <div className="text-[10px] text-muted truncate font-mono">{h.regiao}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1">
                    <BarraProgresso xp={h.xp} xpProx={h.xp_para_prox} />
                  </div>
                  <div className="text-[10px] text-muted font-mono w-[54px] text-right">
                    {h.xp}/{h.xp_para_prox}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Feitos / Wall of Wins (únicos 2 primeiros) */}
          <div className="px-5 py-2 flex items-center justify-between border-t border-border1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              Wall of Wins · Feitos
            </span>
            <span className="text-[10px] text-accent font-bold">
              {FEITOS_PLACEHOLDER.length} conquistas
            </span>
          </div>
          <div className="px-3 pb-3 space-y-1.5 max-h-36 overflow-y-auto">
            {FEITOS_PLACEHOLDER.map((f) => (
              <div key={f.id} className="rounded-lg px-3 py-2 bg-bg2 border border-border1">
                <div className="flex items-start gap-2">
                  <div className="text-[16px] mt-0.5">{f.emoji}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-semibold leading-tight">{f.nome}</div>
                    <div className="text-[10.5px] text-muted leading-relaxed mt-0.5">
                      {f.descricao}
                    </div>
                    <div className="text-[10px] text-muted mt-0.5 font-mono">{f.data}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Sparklines · Hardware */}
          <div className="px-5 py-2 flex items-center justify-between border-t border-border1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              Hardware · 1s
            </span>
            <span className="text-[10px] text-muted">AMD · 5700X3D · 32GB · RX 7600</span>
          </div>
          <div className="px-3 pb-3 grid grid-cols-2 gap-2">
            {[
              { nome: "CPU",     cor: "#F59E0B", pct: 22 },
              { nome: "RAM",     cor: "#3B82F6", pct: 41 },
              { nome: "VRAM",    cor: "#10B981", pct: 58 },
              { nome: "API cnt", cor: "#EF4444", pct: 0  },
            ].map((s) => (
              <div key={s.nome} className="rounded-lg bg-bg2 border border-border1 p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted">
                    {s.nome}
                  </span>
                  <span className="text-[10px] font-mono font-semibold"
                        style={{ color: s.cor }}>{s.pct}%</span>
                </div>
                <Sparkline data={SPARK_FAKE} cor={s.cor} />
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
