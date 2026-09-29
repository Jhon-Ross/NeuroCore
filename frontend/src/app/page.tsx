"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

// ================================================================
// DIA 2 — NEXT.JS CONECTADO NO FASTAPI (http://localhost:8000)
//
// Alteracoes em relacao ao Dia 1:
//   - Textarea HABILITADA e botao Enviar HABILITADO.
//   - Placeholder de "Prometeu esta acordando" REMOVIDO: agora
//     aparece o historico real de mensagens (role user / assistant).
//   - Painel direito RPG NAO EH MAIS PLACEHOLDER: carrega via
//     fetch GET /api_status em useEffect a cada 10s.
//   - Carrega tambem a 1a tela assim que monta.
// ================================================================

const API_BASE = "http://localhost:8000";

// -------- Tipos (alinhados com core/api.py Pydantic) --------

type MensagemChat = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tempo_ms?: number;
  modelo?: string;
  tokens?: number;
  xp?: number;
  timestamp?: number;
};

type HabilidadeUI = {
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

type FeitoUI = {
  id: number;
  nome: string;
  data: string;
  emoji: string;
  descricao: string;
};

type PainelStatus = {
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
  router: { modo_force_local: boolean; openrouter_key_configurada: boolean; teto_mensal_reais: number };
  especialistas: Record<string, { fase: number; is_loaded: boolean; modelo?: string }>;
};

// -------- Fallback local se a API estiver fora (nao quebra UI) --------

const HABILIDADES_FALLBACK: HabilidadeUI[] = [
  { id: "cortex_geral", nome: "Córtex Geral", nivel: 1, xp: 121, xp_para_prox: 100, icone: "🧠", ativo: true, regiao: "llm_core", fase: "1/5" },
  { id: "codigo", nome: "Código", nivel: 0, xp: 0, xp_para_prox: 100, icone: "⚡", regiao: "llm_code", fase: "2/5" },
  { id: "audicao", nome: "Audição", nivel: 0, xp: 0, xp_para_prox: 100, icone: "👂", regiao: "stt_whisper", fase: "3/5" },
  { id: "fonacao", nome: "Fonação", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🗣️", regiao: "tts_xtts", fase: "3/5" },
  { id: "sistema_operacional", nome: "S.O.", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🖥️", regiao: "os_control", fase: "2/5" },
  { id: "visual", nome: "Visual", nivel: 0, xp: 0, xp_para_prox: 100, icone: "👁️", regiao: "image_flux", fase: "5/5" },
  { id: "casa", nome: "Casa Inteligente", nivel: 0, xp: 0, xp_para_prox: 100, icone: "🏠", regiao: "home_control", fase: "4/5" },
];

const FEITOS_FALLBACK: FeitoUI[] = [
  { id: 0, nome: "Marco 0 · Nascimento", data: "27/09/2026", emoji: "🌱", descricao: "Arquitetura NeuroCore aprovada." },
  { id: 2, nome: "Marco 2 · Primeira Palavra", data: "28/09/2026", emoji: "💬", descricao: "Primeira resposta: llama3:latest · 409tok · 526ms." },
];

// Seed deterministica (evita warning hidratacao)
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

// -------- Componentes pequenos --------

function Sparkline({ data, cor }: { data: number[]; cor: string }) {
  const w = 200; const h = 36;
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
      <div className="h-full rounded-full transition-[width] duration-700"
        style={{ width: `${pct}%`, background: "linear-gradient(90deg,#F59E0B 0%,#FBBF24 100%)" }} />
    </div>
  );
}

function formatarDataIso(iso?: string | null, fallback?: string): string {
  if (!iso) return fallback ?? "hoje";
  try {
    const d = new Date(iso);
    const dd = d.getDate().toString().padStart(2, "0");
    const mm = (d.getMonth() + 1).toString().padStart(2, "0");
    const hh = d.getHours().toString().padStart(2, "0");
    const ii = d.getMinutes().toString().padStart(2, "0");
    return `${dd}/${mm} ${hh}:${ii}`;
  } catch { return fallback ?? iso; }
}

// --------- Componente Principal ---------

export default function Home() {
  const [painel, setPainel] = useState<PainelStatus | null>(null);
  const [erroStatus, setErroStatus] = useState<string | null>(null);
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [textoInput, setTextoInput] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Dados de UI (RPG) preferem a API, senao caem em fallback
  const habilidades: HabilidadeUI[] = useMemo(() => {
    const arr = painel?.rpg?.habilidades?.length ? painel.rpg.habilidades : HABILIDADES_FALLBACK;
    // Garante que cortex_geral apareça como ativo se ele for o que tiver maior xp
    return arr.map((h, idx) => ({ ...h, ativo: idx === 0 ? true : (h.ativo ?? (h.nivel > 0 || h.xp > 0)) }));
  }, [painel]);

  const feitos: FeitoUI[] = useMemo(() =>
    (painel?.rpg?.feitos?.length ? painel.rpg.feitos : FEITOS_FALLBACK),
  [painel]);

  const xpGlobalTotal = habilidades.reduce((a, b) => a + b.xp, 0);
  const nivelGlobal = painel?.rpg?.nivel_global ?? 1;
  const xpProxNivel = painel?.rpg?.xp_para_proximo_nivel ?? (nivelGlobal + 1) * 100;
  const xpFaltante = Math.max(0, xpProxNivel - xpGlobalTotal);

  // ---------- Carrega /api/status a cada 10s ----------
  async function carregarStatus(silencioso = false) {
    try {
      const r = await fetch(`${API_BASE}/api/status`, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j: PainelStatus = await r.json();
      setPainel(j);
      setErroStatus(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Falha ao buscar status";
      if (!silencioso) setErroStatus(msg);
    }
  }

  useEffect(() => {
    carregarStatus(false);
    const t = window.setInterval(() => carregarStatus(true), 10000);
    return () => window.clearInterval(t);
  }, []);

  // ---------- Scroll automatico quando chegam msgs ----------
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [mensagens]);

  // ---------- Auto-resize da textarea ----------
  useEffect(() => {
    const t = textareaRef.current;
    if (!t) return;
    t.style.height = "auto";
    t.style.height = Math.min(140, t.scrollHeight) + "px";
  }, [textoInput]);

  // ---------- Enviar mensagem ----------
  async function enviarMensagem() {
    const txt = textoInput.trim();
    if (!txt || enviando) return;

    // 1) Insere imediatamente a msg do usuario
    const idUser = `u-${Date.now()}`;
    const novaUser: MensagemChat = {
      id: idUser, role: "user", content: txt, timestamp: Date.now()
    };
    setMensagens((m) => [...m, novaUser]);
    setTextoInput("");
    setEnviando(true);

    try {
      const body: any = { mensagem: txt, habilidade_alvo: "auto" };
      if (typeof sessionId === "number" && sessionId > 0) body.session_id = sessionId;

      const r = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const txt = await r.text().catch(() => "");
        throw new Error(`HTTP ${r.status}: ${txt.slice(0, 200)}`);
      }
      const j = await r.json();

      // Salva session_id retornada pra este cliente (persiste a sessao no SQLite)
      if (typeof j.session_id === "number" && j.session_id > 0) {
        setSessionId(j.session_id);
      }

      const idBot = `a-${Date.now()}`;
      const msgBot: MensagemChat = {
        id: idBot,
        role: "assistant",
        content: String(j.resposta_texto ?? "⚠️ Sem resposta do Prometeu."),
        tempo_ms: Number(j.tempo_total_ms ?? 0),
        modelo: j.modelo_usado ?? undefined,
        tokens: Number(j.tokens_usados ?? 0),
        xp: Number(j.xp_ganho ?? 0),
        timestamp: Date.now(),
      };
      setMensagens((m) => [...m, msgBot]);

      // Atualiza RPG no painel imediatamente apos resposta para XP aparecer
      setTimeout(() => carregarStatus(true), 250);
    } catch (e) {
      const idBot = `a-${Date.now()}`;
      const err = e instanceof Error ? e.message : "erro desconhecido";
      const msgBot: MensagemChat = {
        id: idBot, role: "assistant",
        content: "⚠️ **Não consegui enviar para o Prometeu.**\n\n"
               + "Certifique-se que `core/api.py` está rodando em http://localhost:8000. Detalhe: " + err,
        timestamp: Date.now(),
      };
      setMensagens((m) => [...m, msgBot]);
    } finally {
      setEnviando(false);
      // Foca de volta no input pra conversar naturalmente
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }

  // ---------- Atalhos de teclado: Enter envia, Shift+Enter nova linha ----------
  function onTextareaKeyDown(ev: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (ev.key === "Enter" && !ev.shiftKey && !ev.nativeEvent.isComposing) {
      ev.preventDefault();
      enviarMensagem();
    }
  }

  const SPARK_FAKE = _seedFake(60, 1337);

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
            <div className="h-8 w-8 rounded-full grid place-items-center bg-accent text-bg0 font-bold select-none">P</div>
            <div className="leading-tight">
              <div className="text-[15px] font-bold text-accent">Prometeu</div>
              <div className="text-[11px] text-muted -mt-0.5">NeuroCore · Fase Embrião</div>
            </div>
          </div>

          <nav className="px-2 py-3 flex flex-col gap-1">
            {[
              { nome: "Chat", ativo: true, ico: "💬" },
              { nome: "Histórico", ativo: false, ico: "📚" },
              { nome: "Rituais", ativo: false, ico: "🌿" },
              { nome: "Memória", ativo: false, ico: "🧠" },
              { nome: "Config.", ativo: false, ico: "⚙️" },
            ].map((m) => (
              <button key={m.nome}
                className={`h-9 w-full px-3 rounded-md flex items-center gap-3 transition
                  ${m.ativo ? "bg-bg3 text-foreground border border-border1"
                           : "text-muted hover:bg-bg2 hover:text-foreground border border-transparent"}`}>
                <span className="text-base">{m.ico}</span>
                <span className="text-[13px] font-medium">{m.nome}</span>
              </button>
            ))}
          </nav>

          <div className="h-px bg-border1 mx-3 my-1" />

          <div className="px-4 pt-3 pb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Sessões</span>
            <button className="text-accent hover:underline text-[11px] font-bold">+ nova</button>
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
            {[
              { nome: "Conversa atual (Dia 2)", data: "29/09 agora", msgs: mensagens.length || 1, ativo: true },
              { nome: "Primeira Palavra", data: "28/09 23:30", msgs: 8, ativo: false },
              { nome: "Planejamento Dia 0", data: "27/09 19:12", msgs: 42, ativo: false },
            ].map((s) => (
              <div key={s.nome}
                className={`h-14 w-full rounded-md px-3 flex flex-col justify-center cursor-pointer transition
                  ${s.ativo ? "bg-bg3 border border-border1" : "hover:bg-bg2 border border-transparent"}`}>
                <div className="flex items-center justify-between">
                  <div className="truncate text-[13px] font-medium">{s.nome}</div>
                  <div className="text-[10px] text-muted ml-2 shrink-0">{s.data}</div>
                </div>
                <div className="text-[11px] text-muted">{s.msgs} mensagens {typeof sessionId === "number" ? "· sessão " + sessionId : ""}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* ============================================================
             COLUNA 2 · CHAT CENTRAL (flex 1fr)
             ============================================================ */}
        <main className="h-full w-full flex flex-col bg-bg0">
          {/* Barra de topo */}
          <div className="h-14 px-6 flex items-center justify-between border-b border-border1 bg-bg1/40 backdrop-blur">
            <div>
              <div className="text-[15px] font-bold">
                Prometeu — Sessão {typeof sessionId === "number" ? sessionId : "nova"}
              </div>
              <div className="text-[11px] text-muted -mt-0.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-success mr-1.5 align-middle" />
                Córtex Geral · {painel?.especialistas?.llm_core?.modelo ?? "llama3:latest"} · RX 7600 8GB · Local 100%
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-8 px-3 rounded-md bg-bg2 border border-border1 text-[11px] text-muted grid place-items-center">
                Modelo: <span className="text-foreground ml-1 font-mono">{painel?.especialistas?.llm_core?.modelo ?? "llama3:latest"}</span>
              </div>
              <div className={`h-8 px-3 rounded-md border text-[11px] grid place-items-center font-semibold
                ${(painel?.router?.modo_force_local ?? true)
                    ? "bg-accent-soft border-accent/40 text-accent"
                    : "bg-bg2 border-border1 text-foreground"}`}>
                Hybrid Router · {(painel?.router?.modo_force_local ?? true) ? "FORCE LOCAL" : "HÍBRIDO"}
              </div>
            </div>
          </div>

          {/* Área de mensagens (REAL agora) */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-14 py-10 flex flex-col justify-start gap-6">
            {mensagens.length === 0 ? (
              <div className="mx-auto max-w-3xl w-full rounded-xl border border-border1 bg-bg1 px-8 py-10 text-center shadow-glow mt-auto mb-auto">
                <div className="text-5xl mb-3">🧠✨</div>
                <div className="text-[20px] font-bold text-accent mb-2">
                  Prometeu está conectado, Jhon!
                </div>
                <div className="text-muted text-[13px] max-w-xl mx-auto leading-relaxed">
                  Escreva algo abaixo para começar. Tente:
                </div>
                <div className="mt-6 flex flex-wrap justify-center gap-2 text-[12px]">
                  {[
                    "Oi Prometeu! Como você está hoje?",
                    "Qual a fórmula do meu nível de RPG?",
                    "Quais são as 7 regiões cerebrais?",
                  ].map((ex) => (
                    <button key={ex}
                      onClick={() => setTextoInput(ex)}
                      className="px-3 py-2 rounded-lg bg-bg2 border border-border1 text-foreground hover:bg-bg3 hover:border-accent/50 transition">
                      {ex}
                    </button>
                  ))}
                </div>
                <div className="mt-6 flex flex-wrap justify-center gap-2 text-[11px]">
                  {[
                    "LangGraph · SQLite ACID",
                    "Ollama · DirectML · AMD RX 7600",
                    "XP por interação · Wall of Wins",
                  ].map((t) => (
                    <span key={t} className="px-3 py-1 rounded-full bg-bg3 border border-border1 text-muted">
                      {t}
                    </span>
                  ))}
                </div>
                {erroStatus && (
                  <div className="mt-4 text-[12px] rounded-md border border-danger/50 bg-danger/10 text-danger px-4 py-2 inline-block">
                    ⚠️ FastAPI :8000 offline: {erroStatus}
                  </div>
                )}
              </div>
            ) : (
              mensagens.map((m) => (
                <div key={m.id} className={`w-full flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl px-5 py-3 border whitespace-pre-wrap break-words shadow
                    ${m.role === "user"
                        ? "bg-accent/95 text-bg0 border-accent rounded-br-sm"
                        : "bg-bg1 text-foreground border-border1 rounded-bl-sm"}`}>
                    <div className="text-[13.5px] leading-relaxed">{m.content}</div>
                    {m.role === "assistant" && (
                      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10.5px] opacity-80">
                        {typeof m.tempo_ms === "number" && (
                          <span>⏱️ {Math.round(m.tempo_ms)}ms</span>
                        )}
                        {typeof m.tokens === "number" && m.tokens > 0 && (
                          <span>🎟️ {m.tokens} tokens</span>
                        )}
                        {m.modelo && (
                          <span className="font-mono">🤖 {m.modelo}</span>
                        )}
                        {typeof m.xp === "number" && m.xp > 0 && (
                          <span className="font-bold">✨ +{m.xp} XP</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {enviando && (
              <div className="w-full flex justify-start">
                <div className="rounded-2xl rounded-bl-sm bg-bg1 border border-border1 px-5 py-3">
                  <div className="flex items-center gap-2 text-[12px] text-muted">
                    <span className="inline-flex gap-1">
                      <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                      <span className="h-2 w-2 rounded-full bg-accent/70 animate-pulse [animation-delay:120ms]" />
                      <span className="h-2 w-2 rounded-full bg-accent/40 animate-pulse [animation-delay:240ms]" />
                    </span>
                    Prometeu está pensando…
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Caixa de input (habilitada, conectada real) */}
          <div className="h-auto min-h-[112px] px-14 pb-6 pt-4 border-t border-border1 bg-bg1/40">
            <div className="mx-auto max-w-3xl w-full grid grid-cols-[1fr_auto] gap-3">
              <textarea
                ref={textareaRef}
                value={textoInput}
                onChange={(e) => setTextoInput(e.target.value)}
                onKeyDown={onTextareaKeyDown}
                placeholder="Digite algo para o Prometeu… (Enter envia, Shift+Enter nova linha)"
                disabled={enviando}
                rows={2}
                className="min-h-[64px] max-h-[140px] w-full resize-none rounded-xl bg-bg2 border border-border1 px-4 py-3
                           text-[13px] text-foreground placeholder:text-muted/60 outline-none
                           focus:ring-2 focus:ring-accent/40 focus:border-accent/60
                           disabled:opacity-50"
              />
              <button
                onClick={enviarMensagem}
                disabled={enviando || !textoInput.trim()}
                className="h-auto self-stretch px-5 rounded-xl bg-accent text-bg0 font-bold text-[13px]
                           disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110 transition grid place-items-center">
                {enviando ? "…" : "↵ Enviar"}
              </button>
            </div>
            <div className="mx-auto max-w-3xl w-full mt-2 text-[10.5px] text-muted flex items-center justify-between">
              <div>
                API FastAPI:
                <span className={`ml-1.5 font-mono ${erroStatus ? "text-danger" : "text-success"} font-bold`}>
                  {erroStatus ? "OFFLINE" : "http://localhost:8000"}
                </span>
                {typeof sessionId === "number" && <span className="ml-3">Sessão SQLite: <span className="font-mono">#{sessionId}</span></span>}
              </div>
              <div>Respostas são privadas 100% · sem dados fora do seu PC</div>
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
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Nível Global</span>
              <span className="h-6 px-2 rounded-md bg-accent-soft border border-accent/40 text-accent text-[11px] font-bold grid place-items-center">
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
                <div className="text-[22px] font-bold text-accent leading-none">{feitos.length}</div>
              </div>
            </div>
            <BarraProgresso xp={xpGlobalTotal} xpProx={xpProxNivel} />
          </div>

          {/* 7 Habilidades */}
          <div className="px-5 pt-3 pb-1 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">7 Habilidades · Regiões</span>
            <span className="text-[10px] text-muted">Fase N/5</span>
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5">
            {habilidades.map((h) => (
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
                          <span className="ml-1.5 text-[9px] font-bold uppercase tracking-wider text-success">● ativa</span>
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

          {/* Wall of Wins */}
          <div className="px-5 py-2 flex items-center justify-between border-t border-border1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Wall of Wins · Feitos</span>
            <span className="text-[10px] text-accent font-bold">{feitos.length} conquistas</span>
          </div>
          <div className="px-3 pb-3 space-y-1.5 max-h-36 overflow-y-auto">
            {feitos.map((f) => (
              <div key={f.id} className="rounded-lg px-3 py-2 bg-bg2 border border-border1">
                <div className="flex items-start gap-2">
                  <div className="text-[16px] mt-0.5">{f.emoji}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-semibold leading-tight">{f.nome}</div>
                    <div className="text-[10.5px] text-muted leading-relaxed mt-0.5">{f.descricao}</div>
                    <div className="text-[10px] text-muted mt-0.5 font-mono">{formatarDataIso(null, f.data)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Sparklines Hardware */}
          <div className="px-5 py-2 flex items-center justify-between border-t border-border1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Hardware · 10s</span>
            <span className="text-[10px] text-muted">AMD · 5700X3D · 32GB · RX 7600</span>
          </div>
          <div className="px-3 pb-3 grid grid-cols-2 gap-2">
            {[
              { nome: "CPU",  cor: "#F59E0B", pct: 22 },
              { nome: "RAM",  cor: "#3B82F6", pct: 41 },
              { nome: "VRAM", cor: "#10B981", pct: Math.round((painel?.vram?.total_gb ?? 0) * 12.5 || 0) },
              { nome: "XP/m", cor: "#EF4444", pct: Math.min(100, Math.round(xpGlobalTotal / 10 || 0)) },
            ].map((s) => (
              <div key={s.nome} className="rounded-lg bg-bg2 border border-border1 p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted">{s.nome}</span>
                  <span className="text-[10px] font-mono font-semibold" style={{ color: s.cor }}>{s.pct}%</span>
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
