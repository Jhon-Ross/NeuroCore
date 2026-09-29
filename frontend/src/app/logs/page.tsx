"use client";

// ================================================================
// PÁGINA /logs · CONSOLE AO VIVO DO LAUNCHER
// 3 abas: FastAPI (stdout+stderr), Prometeu JSONL, Ollama logs
// Integracao tail_logs Rust a ser conectada na Task 6 — MVP polling
// ================================================================

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTauriEnv } from "../../components/use_tauri_env";
import { usePainelStatus } from "../../components/use_painel_status";
import { CirculoStatus, Card } from "../../components/ui_utils";
import type { ServicoNome } from "../../components/types";

type Aba = "fastapi" | "jsonl" | "ollama";
type Nivel = "INFO" | "WARN" | "ERROR" | "DEBUG";

type LinhaLog = {
  id: number;
  kind: Aba;
  ts: string;
  nivel: Nivel;
  tag?: string;
  msg: string;
  raw: string;
};

const ABAS: { id: Aba; nome: string; desc: string; ico: string }[] = [
  { id: "fastapi", nome: "1 · FastAPI STDOUT", desc: "uvicorn :8000 — stdout + stderr", ico: "🔌" },
  { id: "jsonl",   nome: "2 · Prometeu JSONL", desc: "Logger estruturado G:\\memory\\logs\\YYYY-MM-DD.jsonl", ico: "🧠" },
  { id: "ollama",  nome: "3 · Ollama Stdout",  desc: "ollama serve :11434", ico: "🐳" },
];

const NIVEIS_FILTRO: (Nivel | "ALL")[] = ["ALL", "INFO", "WARN", "ERROR", "DEBUG"];

function corLinha(nivel: Nivel, kind: Aba) {
  if (nivel === "ERROR") return "text-danger";
  if (nivel === "WARN")  return "text-yellow-300";
  if (kind === "jsonl")  return "text-blue-200";
  if (kind === "ollama") return "text-emerald-200";
  return "text-foreground";
}

export default function LogsPage() {
  const tauri = useTauriEnv();
  const ps = usePainelStatus(4000);
  const [aba, setAba] = useState<Aba>("jsonl");
  const [nivel, setNivel] = useState<(Nivel | "ALL")>("ALL");
  const [tag, setTag] = useState<string>("ALL");
  const [pausado, setPausado] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [buffer, setBuffer] = useState<LinhaLog[]>([]);
  const [cursor, setCursor] = useState(1);
  const scrollRef = useRef<HTMLDivElement>(null);
  const refBottom = useRef<HTMLDivElement>(null);

  // Demo seed de linhas APENAS quando !tauri.isTauri
  useEffect(() => {
    if (tauri.isTauri) return;
    if (pausado) return;
    const t = window.setInterval(() => {
      const demos = [
        { kind: "fastapi" as const, ts: new Date().toISOString(), nivel: "INFO" as const, msg: `INFO: ${new Date().toLocaleTimeString("pt-BR")} GET /api/status 200 OK ${Math.round(30 + Math.random() * 80)}ms` },
        { kind: "jsonl"   as const, ts: new Date().toISOString(), nivel: "INFO" as const, tag: "orquestrador", msg: `router: resolveu rota [${["cortex_geral","codigo","sistema_operacional","llm_core"][Math.floor(Math.random()*4)]}] heurística keywords.` },
        { kind: "jsonl"   as const, ts: new Date().toISOString(), nivel: "INFO" as const, tag: "rpg", msg: `+${2 + Math.floor(Math.random() * 10)} XP adquirido (habilidade).` },
        { kind: "jsonl"   as const, ts: new Date().toISOString(), nivel: "DEBUG" as const, tag: "vram", msg: `ollama probe ps: ${1 + Math.floor(Math.random() * 2)} modelos carregados.` },
        { kind: "ollama"  as const, ts: new Date().toISOString(), nivel: "INFO" as const, msg: `[router] POST /v1/chat/completions -> llama3:latest ${400 + Math.floor(Math.random()*800)} tok/s` },
      ];
      const raw_ = demos.map((d) => `${d.ts} [${d.nivel}] ${d.tag ? `(${d.tag}) ` : ""}${d.msg}`);
      const extra: LinhaLog[] = demos.map<LinhaLog>((d, i) => ({ ...d, id: cursor + i, raw: raw_[i] }));
      setCursor((c) => c + demos.length);
      setBuffer((b) => {
        const prox = [...b, ...extra];
        return prox.length > 2000 ? prox.slice(prox.length - 2000) : prox;
      });
    }, 1600);
    return () => window.clearInterval(t);
  }, [pausado, cursor, tauri.isTauri]);

  // Inicia tails via Rust e escuta eventos log://line quando rodando em Tauri
  useEffect(() => {
    if (!tauri.isTauri) return;
    let unlisten: (() => void) | undefined;

    (async () => {
      try {
        await Promise.all([
          tauri.invoke<any>("tail_logs", { kind: "fastapi", stop: false }).catch(() => {}),
          tauri.invoke<any>("tail_logs", { kind: "jsonl",   stop: false }).catch(() => {}),
          tauri.invoke<any>("tail_logs", { kind: "ollama",  stop: false }).catch(() => {}),
        ]);
        console.info("[logs] tails iniciados.");
      } catch (e) {
        console.warn("[logs] erro ao iniciar tails:", e);
      }

      try {
        unlisten = await tauri.listen("log://line", (p: any) => {
          if (!p || !p.kind) return;
          const kindSafe = (["fastapi", "jsonl", "ollama"] as Aba[]).includes(p.kind as Aba)
            ? (p.kind as Aba)
            : ("jsonl" as Aba);
          let nivel: Nivel = "INFO";
          if (p.level) {
            const up = String(p.level).toUpperCase();
            if (up === "ERROR") nivel = "ERROR";
            else if (up === "WARN" || up === "WARNING") nivel = "WARN";
            else if (up === "DEBUG") nivel = "DEBUG";
            else if (up === "INFO") nivel = "INFO";
          }
          setBuffer((b) => {
            const novoId = (b[b.length - 1]?.id ?? 0) + 1;
            const nova: LinhaLog = {
              id: novoId,
              kind: kindSafe,
              ts: p.ts || new Date().toISOString(),
              nivel,
              tag: p.tag,
              msg: p.msg ?? p.raw ?? "",
              raw: p.raw ?? "",
            };
            const prox = [...b, nova];
            return prox.length > 2000 ? prox.slice(prox.length - 2000) : prox;
          });
        });
      } catch (e) {
        console.warn("[logs] erro ao escutar log://line:", e);
      }
    })();

    return () => {
      if (unlisten) {
        try { unlisten(); } catch {}
      }
      (async () => {
        try {
          await Promise.all([
            tauri.invoke<any>("tail_logs", { kind: "fastapi", stop: true }).catch(() => {}),
            tauri.invoke<any>("tail_logs", { kind: "jsonl",   stop: true }).catch(() => {}),
            tauri.invoke<any>("tail_logs", { kind: "ollama",  stop: true }).catch(() => {}),
          ]);
        } catch {}
      })();
    };
  }, [tauri.isTauri]);

  // Auto scroll
  useEffect(() => {
    if (autoScroll && refBottom.current) {
      refBottom.current.scrollIntoView({ block: "end", behavior: "smooth" });
    }
  }, [buffer, aba, autoScroll]);

  const tagsUnicas = useMemo(() => {
    const s = new Set<string>();
    buffer.forEach((b) => { if (b.tag) s.add(b.tag); });
    return ["ALL", ...Array.from(s).sort()];
  }, [buffer]);

  const linhasAba = useMemo(() => buffer.filter((l) => l.kind === aba), [buffer, aba]);
  const linhasFiltradas = useMemo(() => {
    return linhasAba.filter((l) => {
      if (nivel !== "ALL" && l.nivel !== nivel) return false;
      if (tag !== "ALL" && l.tag !== tag) return false;
      return true;
    });
  }, [linhasAba, nivel, tag]);

  function limpar() {
    setBuffer((b) => b.filter((x) => x.kind !== aba));
  }
  async function copiar500() {
    const ult500 = linhasFiltradas.slice(-500).map((l) => l.raw || `${l.ts} [${l.nivel}] ${l.tag ? "("+l.tag+") " : ""}${l.msg}`).join("\n");
    try {
      if (navigator?.clipboard?.writeText) await navigator.clipboard.writeText(ult500);
      alert("✓ Últimas 500 linhas copiadas!");
    } catch {
      alert("Erro ao copiar.");
    }
  }
  async function exportarTxt() {
    const txt = linhasFiltradas.map((l) => l.raw || `${l.ts} [${l.nivel}] ${l.tag ? "("+l.tag+") " : ""}${l.msg}`).join("\n");
    try {
      const blob = new Blob([txt], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `neurocore_${aba}_${Date.now()}.log`; a.click();
      URL.revokeObjectURL(url);
    } catch {}
  }
  async function reconnectar() {
    try {
      const res = await tauri.invoke<any>("tail_logs", { kind: aba, stop: false });
      console.info("[logs] reconnect tail_logs:", res);
    } catch {}
  }

  const coresAba: Record<Aba, string> = {
    fastapi: "text-blue-200 border-blue-500/50",
    jsonl:   "text-accent  border-accent/50",
    ollama:  "text-emerald-200 border-emerald-500/50",
  };

  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-bg0">
      {/* Cabecalho */}
      <div className="px-6 py-4 border-b border-border1 bg-bg1/50 shrink-0">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-[20px] font-bold flex items-center gap-2">
              📜 Console de Logs <span className="text-muted text-[12px] font-normal">Ao vivo</span>
            </h1>
            <p className="text-[12px] text-muted mt-0.5">
              Integração com Rust <code className="px-1 bg-bg2 rounded border border-border1 mx-1">tail_logs</code> (Task 6).
              No momento, exibe um stream demo enquanto o backend não é ligado.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={() => setPausado((p) => !p)}
              className={"h-9 px-3 rounded-md text-[12px] font-semibold border " +
                (pausado
                  ? "bg-amber-500/10 text-amber-300 border-amber-400/40"
                  : "bg-bg2 border-border1 text-foreground hover:bg-bg3")}>
              {pausado ? "▶ Retomar" : "⏸ Pausar"}
            </button>
            <button onClick={() => setAutoScroll((x) => !x)}
              className={"h-9 px-3 rounded-md text-[12px] font-semibold border " +
                (autoScroll
                  ? "bg-accent-soft text-accent border-accent/40"
                  : "bg-bg2 border-border1 text-foreground hover:bg-bg3")}>
              Auto-scroll {autoScroll ? "ON" : "OFF"}
            </button>
            <button onClick={limpar}
              className="h-9 px-3 rounded-md bg-bg2 border border-border1 hover:bg-danger/10 hover:text-danger text-[12px]">
              🧹 Limpar
            </button>
            <button onClick={copiar500}
              className="h-9 px-3 rounded-md bg-bg2 border border-border1 hover:bg-bg3 text-[12px]">
              📋 Copiar 500
            </button>
            <button onClick={exportarTxt}
              className="h-9 px-3 rounded-md bg-bg3 hover:bg-accent hover:text-bg0 border border-border1 hover:border-accent text-[12px] font-semibold">
              💾 Exportar .log
            </button>
            <button onClick={reconnectar}
              className="h-9 px-3 rounded-md bg-success/10 border border-success/40 text-success text-[12px] font-semibold hover:bg-success/20">
              ↻ Reconnectar Rust
            </button>
          </div>
        </div>

        {/* 3 abas */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2">
          {ABAS.map((a) => {
            const contagem = linhasAba.filter((l) => l.kind === a.id).length; // compat pq ja filtramos; sempre igual
            const contaTotal = buffer.filter((l) => l.kind === a.id).length;
            const active = aba === a.id;
            return (
              <button key={a.id} onClick={() => setAba(a.id)}
                className={"text-left rounded-lg px-4 py-3 border transition " +
                  (active
                    ? `bg-bg2 ${coresAba[a.id].split(" ")[1]} shadow-[0_0_0_1px_rgba(245,158,11,0.18)]`
                    : "bg-bg1/60 border-border1 hover:bg-bg2")}>
                <div className="flex items-center justify-between mb-0.5">
                  <div className="text-[13px] font-bold flex items-center gap-2">
                    <span>{a.ico}</span>
                    <span className={active ? coresAba[a.id].split(" ")[0] : "text-foreground"}>{a.nome}</span>
                  </div>
                  <span className="text-[10.5px] text-muted font-mono">{contaTotal} linhas</span>
                </div>
                <div className="text-[11px] text-muted">{a.desc}</div>
              </button>
            );
          })}
        </div>

        {/* Filtros */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted mr-1">Filtros</span>
          <div className="flex items-center gap-1 rounded-md bg-bg2 border border-border1 p-1">
            {NIVEIS_FILTRO.map((n) => (
              <button key={n} onClick={() => setNivel(n)}
                className={"h-7 px-2.5 rounded text-[11px] font-mono font-semibold transition " +
                  (nivel === n
                    ? (n === "ERROR" ? "bg-danger text-bg0"
                      : n === "WARN" ? "bg-yellow-400 text-bg0"
                      : n === "DEBUG" ? "bg-purple-400 text-bg0"
                      : n === "INFO" ? "bg-blue-500 text-bg0"
                      : "bg-accent text-bg0")
                    : "text-muted hover:text-foreground")}>
                {n}
              </button>
            ))}
          </div>

          <select value={tag} onChange={(e) => setTag(e.target.value)}
            className="h-8 px-2 rounded-md bg-bg2 border border-border1 text-[12px] outline-none focus:ring-2 focus:ring-accent/40">
            {tagsUnicas.map((t) => (
              <option key={t} value={t}>tag: {t}</option>
            ))}
          </select>

          <div className="ml-auto flex items-center gap-2 text-[11.5px] text-muted">
            <CirculoStatus online={!pausado && tauri.isTauri} />
            <span>
              {aba === "fastapi" ? "Proveniente:" :
               aba === "jsonl"   ? "Fonte:" :
                                   "Fonte:"}{" "}
              <span className="text-foreground font-semibold">{
                aba === "fastapi" ? "Rust tail LogKind::FastApi" :
                aba === "jsonl"   ? "G:/memory/logs/2026-09-29.jsonl" :
                                    "Rust tail LogKind::Ollama"
              }</span>
            </span>
            <span className="font-mono">· {linhasFiltradas.length} / {linhasAba.length} linhas</span>
          </div>
        </div>
      </div>

      {/* Log body — terminal-like */}
      <div ref={scrollRef}
           className="flex-1 overflow-y-auto bg-[#050507] font-mono text-[11.5px] leading-6 px-4 py-3 min-h-0 border-t border-black/60">
        {linhasFiltradas.length === 0 ? (
          <div className="text-muted italic mt-8">Aguardando linhas… Conecte o Rust tail_logs na Task 6.</div>
        ) : (
          <div className="space-y-0.5">
            {linhasFiltradas.map((l, idx) => {
              const nivelColor =
                l.nivel === "ERROR" ? "text-danger font-bold" :
                l.nivel === "WARN"  ? "text-yellow-300" :
                l.nivel === "DEBUG" ? "text-purple-300" :
                "text-blue-300";
              return (
                <div key={`${l.id}-${idx}`} className="flex flex-wrap gap-x-2 items-baseline hover:bg-white/[0.02] px-1 -mx-1 rounded">
                  <span className="text-muted w-[82px] shrink-0">{l.ts.slice(11, 19)}</span>
                  <span className={`uppercase font-bold ${nivelColor} w-[58px] shrink-0`}>{l.nivel}</span>
                  {l.tag && (
                    <span className="px-1.5 py-0.5 rounded bg-bg2 border border-border1 text-[10.5px] text-accent w-[96px] truncate shrink-0 inline-block align-middle">
                      {l.tag}
                    </span>
                  )}
                  <span className={`flex-1 break-words min-w-[200px] ${corLinha(l.nivel, l.kind)}`}>
                    {l.msg}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        <div ref={refBottom} />
      </div>

      {/* Rodape mini estatisticas */}
      <div className="h-8 px-4 border-t border-border1 bg-bg1/60 text-[10.5px] text-muted flex items-center justify-between shrink-0">
        <div className="font-mono">
          API :8000 · {ps.erro ? <span className="text-danger">OFFLINE</span> : <span className="text-success">ONLINE</span>} ·
          {" "}Ollama :11434 · {(ps.painel?.vram.online) ? <span className="text-success">ONLINE</span> : <span className="text-muted">detectando…</span>}
        </div>
        <div className="font-mono">
          Memória: R$ 0,00 · GPU AMD Radeon RX 7600 · DirectML
        </div>
      </div>
    </div>
  );
}
