"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PainelDireito } from "./PainelDireito";
import { CirculoStatus, formatarUptime } from "./ui_utils";
import { CustomTitlebar } from "./CustomTitlebar";
import { useTauriEnv } from "./use_tauri_env";
import { useLauncherConfig } from "./use_launcher_config";
import type { StatusServico, ServicoNome } from "./types";

// ================================================================
// SHELL 3 COLUNAS PRINCIPAL DO LAUNCHER — LAYOUT PERMANENTE
// Sidebar 240px / Centro 1fr / Direito 320px
// ================================================================

const NAV_ITENS: { id: string; rota: string; nome: string; ico: string }[] = [
  { id: "dashboard",    rota: "/",             nome: "Dashboard",    ico: "📊" },
  { id: "chat",         rota: "/chat",         nome: "Chat Web",     ico: "💬" },
  { id: "logs",         rota: "/logs",         nome: "Console",      ico: "📜" },
  { id: "especialistas",rota: "/especialistas",nome: "Especialistas",ico: "🧬" },
];

const SERVICOS_INICIAL: Record<ServicoNome, StatusServico> = {
  ollama:   { nome: "ollama",   rotulo: "Ollama",         icone: "🧠", online: false, porta: 11434 },
  api:      { nome: "api",      rotulo: "API Prometeu",   icone: "🔌", online: false, porta: 8000  },
  frontend: { nome: "frontend", rotulo: "Frontend :3000", icone: "🎨", online: false, porta: 3000  },
  chatcli:  { nome: "chatcli",  rotulo: "Chat CLI",       icone: "⌨️", online: false },
};

// Mapea nome do serviço Rust → ServicoNome frontend (1:1 direto)
function mapServicoRust(nome: ServicoNome, rust: any, fallback: StatusServico): StatusServico {
  if (!rust || typeof rust !== "object") return fallback;
  return {
    ...fallback,
    online: !!rust.online,
    pid: typeof rust.pid === "number" ? rust.pid : fallback.pid,
    porta: typeof rust.port === "number" ? rust.port : fallback.porta,
    uptime_segundos:
      typeof rust.uptime_segundos === "number"
        ? rust.uptime_segundos
        : typeof rust.uptime === "number"
          ? rust.uptime
          : fallback.uptime_segundos,
    memoria_mb:
      typeof rust.memoria_mb === "number"
        ? rust.memoria_mb
        : typeof rust.memory_mb === "number"
          ? rust.memory_mb
          : fallback.memoria_mb,
  };
}

export default function LauncherShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname() ?? "/";
  const tauri = useTauriEnv();
  const lc = useLauncherConfig();
  const [servicos, setServicos] = useState<Record<ServicoNome, StatusServico>>(SERVICOS_INICIAL);
  const [busyEnergia, setBusyEnergia] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tipo: "ok" | "erro" | "info"; msg: string; ts: number } | null>(null);

  // ---------------------------------------------------------------------------
  // Task 5: polling check_services() a cada 4s no ambiente Tauri
  // ---------------------------------------------------------------------------
  async function sondaServicos(silencioso = true) {
    try {
      const s: any = await tauri.invoke("check_services");
      if (s && typeof s === "object") {
        setServicos((ant) => ({
          ollama:   mapServicoRust("ollama",   s.ollama,   ant.ollama),
          api:      mapServicoRust("api",      s.api,      ant.api),
          frontend: mapServicoRust("frontend", s.frontend, ant.frontend),
          chatcli:  mapServicoRust("chatcli",  s.chatcli,  ant.chatcli),
        }));
      }
    } catch {
      if (!silencioso) {
        // Modo navegador: heurística simples sonda HTTP diretamente
        try {
          const [o, a, f] = await Promise.allSettled([
            fetch("http://127.0.0.1:11434/api/tags", { method: "HEAD" }).then((r) => r.ok),
            fetch("http://127.0.0.1:8000/api/status", { cache: "no-store" }).then((r) => r.ok),
            fetch("http://localhost:3000/", { method: "HEAD" }).then((r) => r.ok),
          ]);
          setServicos((ant) => ({
            ...ant,
            ollama:   { ...ant.ollama,   online: o.status === "fulfilled" && !!o.value },
            api:      { ...ant.api,      online: a.status === "fulfilled" && !!a.value },
            frontend: { ...ant.frontend, online: f.status === "fulfilled" && !!f.value },
          }));
        } catch {}
      }
    }
  }

  useEffect(() => {
    sondaServicos(false);
    const intervalo = lc.cfg.poll_interval_ms ?? 4000;
    const t = window.setInterval(
      () => sondaServicos(true),
      tauri.isTauri ? intervalo : Math.max(8000, intervalo),
    );
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tauri.isTauri, lc.cfg.poll_interval_ms]);

  async function acaoEnergia(acao: "ligar" | "desligar" | "toggle", nome?: ServicoNome) {
    if (busyEnergia) return;

    // Fallback MODO NAVEGADOR (preview standalone :3000 / TRAE preview)
    // NÃO é o caso do Tauri Desktop WebView2 (lá tauri.isTauri = true).
    // Apenas para quando o usuário abre http://localhost:3000 diretamente no Chrome/Edge
    // fora do launcher (ainda tem direito a feedback e re-sonda).
    if (!tauri.isTauri) {
      setFeedback({
        tipo: "erro",
        ts: Date.now(),
        msg:
          acao === "ligar"
            ? "⚠️ Você abriu no navegador (Chrome/Edge), não no Launcher Desktop. Para Ligar os serviços, abra pelo atalho 'NeuroCore Launcher.lnk' na Área de Trabalho (abre WebView2 do Tauri). Re-sondando portas já existentes..."
            : acao === "desligar"
              ? "⚠️ Modo navegador: Para Desligar use scripts/scripts/parar_prometeu.ps1 ou abra pelo launcher desktop. Re-sondando portas..."
              : `⚠️ Modo navegador: toggle do serviço ${nome} indisponível. Abra pelo Launcher Desktop. Re-sondando...`,
      });
      if (acao === "ligar" || acao === "desligar") {
        const cmd = acao === "ligar" ? "start_all" : "stop_all";
        setBusyEnergia(cmd);
      } else if (nome) {
        setBusyEnergia(nome);
      }
      for (let i = 0; i < 4; i++) {
        await new Promise((r) =>
          setTimeout(r, i === 0 ? 800 : i === 1 ? 2000 : i === 2 ? 4000 : 8000),
        );
        sondaServicos(true);
      }
      setTimeout(() => setBusyEnergia(null), 300);
      setTimeout(() => setFeedback(null), 14000);
      return;
    }

    try {
      if (acao === "ligar" || acao === "desligar") {
        const cmd = acao === "ligar" ? "start_all" : "stop_all";
        const include_ollama =
          acao === "ligar" ? true : !lc.cfg.manter_ollama_vivo_ao_sair;
        setBusyEnergia(cmd);
        setFeedback({
          tipo: "info",
          ts: Date.now(),
          msg:
            cmd === "start_all"
              ? "▶️ Iniciando cascata: Ollama → API Prometeu :8000 → Frontend :3000 (aguarde 10-30s)…"
              : "🛑 Desligando serviços (Ollama vivo mantido)…",
        });
        const ret = await tauri.invoke<string>(cmd, { include_ollama });
        setFeedback({
          tipo: "ok",
          ts: Date.now(),
          msg: ret || (cmd === "start_all" ? "Serviços iniciados." : "Serviços desligados."),
        });
      } else if (acao === "toggle" && nome) {
        const agora = servicos[nome].online;
        const cmd = agora ? "stop_service" : "start_service";
        setBusyEnergia(nome);
        setFeedback({
          tipo: "info",
          ts: Date.now(),
          msg: `${agora ? "🛑 Parando" : "▶️ Iniciando"} serviço ${nome}…`,
        });
        const ret = await tauri.invoke<string>(cmd, { name: nome });
        setFeedback({
          tipo: "ok",
          ts: Date.now(),
          msg: ret || "Comando enviado.",
        });
      }
      for (let i = 0; i < 4; i++) {
        await new Promise((r) =>
          setTimeout(r, i === 0 ? 1000 : i === 1 ? 3000 : i === 2 ? 6000 : 12000),
        );
        sondaServicos(true);
      }
    } catch (e: any) {
      console.error("Ação energia falhou:", e);
      setFeedback({
        tipo: "erro",
        ts: Date.now(),
        msg: e?.message || e?.toString() || "Falha na ação de energia (veja DevTools F12).",
      });
    } finally {
      setTimeout(() => setBusyEnergia(null), 200);
      setTimeout(() => setFeedback(null), 12000);
    }
  }

  async function abrirAtalho(kind: "chat" | "swagger" | "tags" | "memoria" | "projeto") {
    if (tauri.isTauri && (kind === "memoria" || kind === "projeto")) {
      try {
        await tauri.invoke<any>("open_in_explorer", { kind });
        return;
      } catch {}
    }
    const u =
      kind === "chat"     ? "http://localhost:3000/chat" :
      kind === "swagger"  ? "http://127.0.0.1:8000/docs" :
      kind === "tags"     ? "http://127.0.0.1:11434/" :
      kind === "memoria"  ? "file:///G:/memory" :
                            "file:///C:/Users/Jhon%20Ross/Documents/trae_projects/NeuroCore/";
    await tauri.shellOpen(u);
  }

  return (
    <div
      suppressHydrationWarning
      className="h-screen w-screen max-h-screen max-w-screen overflow-hidden bg-bg0 text-foreground font-sans text-[13px]"
    >
      <CustomTitlebar />
      <div
        suppressHydrationWarning
        className="w-full grid overflow-hidden"
        style={{ height: "calc(100% - 32px)", gridTemplateColumns: "240px 1fr 320px", gap: "0px" }}
      >
        {/* COLUNA 1 · SIDEBAR */}
        <aside className="h-full w-full bg-bg1 border-r border-border1 flex flex-col" suppressHydrationWarning>
          <div className="h-14 px-4 flex items-center gap-3 border-b border-border1 shrink-0">
            <div className="h-8 w-8 rounded-full grid place-items-center bg-accent text-bg0 font-bold select-none">P</div>
            <div className="leading-tight min-w-0">
              <div className="text-[15px] font-bold text-accent truncate">NeuroCore</div>
              <div className="text-[11px] text-muted -mt-0.5 truncate">Painel · Launcher Desktop</div>
            </div>
          </div>

          {/* Energia */}
          <div className="px-3 pt-3 pb-2 space-y-2 shrink-0 border-b border-border1">
            <button
              disabled={!!busyEnergia}
              onClick={() => acaoEnergia("ligar")}
              className={
                "h-9 w-full rounded-md flex items-center justify-center gap-2 font-semibold text-[13px] " +
                "transition disabled:opacity-50 disabled:cursor-not-allowed " +
                (tauri.isTauri
                  ? "bg-accent text-bg0 hover:brightness-110"
                  : "bg-bg2 text-muted border border-border1 hover:border-accent/30 hover:text-foreground cursor-pointer")
              }
              title={
                !tauri.isTauri
                  ? "Modo navegador: Ligar/Desligar não usa Rust IPC (sonda portas). Para controle real, abra pelo atalho 'NeuroCore Launcher.lnk' na Área de Trabalho."
                  : busyEnergia === "start_all"
                    ? "Iniciando serviços…"
                    : "▶️ Ligar Tudo: Ollama → API :8000 → Frontend :3000"
              }
            >
              {busyEnergia === "start_all" ? "⏳ Ligando serviços…" : "▶️ Ligar Tudo"}
            </button>
            <button
              disabled={!!busyEnergia}
              onClick={() => acaoEnergia("desligar")}
              className={
                "h-8 w-full rounded-md flex items-center justify-center gap-2 text-[12px] " +
                "transition disabled:opacity-50 disabled:cursor-not-allowed " +
                (tauri.isTauri
                  ? "bg-bg3 border border-danger/40 text-danger hover:bg-danger/10"
                  : "bg-bg2 border border-border1 text-muted hover:border-danger/30 hover:text-danger cursor-pointer")
              }
              title={
                !tauri.isTauri
                  ? "Modo navegador: use scripts/parar_prometeu.ps1 para desligar serviços reais. Aqui apenas re-sonda."
                  : busyEnergia === "stop_all"
                    ? "Desligando serviços…"
                    : "🛑 Desligar Tudo (mantém Ollama vivo por padrão)"
              }
            >
              {busyEnergia === "stop_all" ? "⏳ Desligando serviços…" : "🛑 Desligar Tudo"}
            </button>

            {/* 4 Toggles serviços */}
            <div className="grid grid-cols-2 gap-1.5 pt-1">
              {(Object.values(servicos) as StatusServico[]).map((s) => {
                const sublinha = s.online
                  ? (
                      <>
                        <span className="truncate">
                          {s.porta ? `:${s.porta} · ` : ""}
                          {s.pid ? `PID ${s.pid}` : "online"}
                          {s.memoria_mb ? ` · ${Math.round(s.memoria_mb)} MB` : ""}
                        </span>
                        {typeof s.uptime_segundos === "number" && s.uptime_segundos > 0 && (
                          <span className="hidden sm:block truncate">
                            uptime {formatarUptime(s.uptime_segundos)}
                          </span>
                        )}
                      </>
                    )
                  : `offline${s.porta ? ` · :${s.porta}` : ""}`;
                return (
                  <button
                    key={s.nome}
                    disabled={!!busyEnergia}
                    onClick={() => acaoEnergia("toggle", s.nome)}
                    className={
                      "h-auto min-h-[56px] px-2 py-1.5 rounded-md flex flex-col justify-center items-start border text-left transition " +
                      (s.online
                        ? "bg-bg3 border-success/30 "
                        : "bg-bg2 border-border1 hover:border-accent/40 ") +
                      (!!busyEnergia ? "opacity-60 cursor-not-allowed" : "")
                    }
                    title={
                      !tauri.isTauri
                        ? `Modo navegador: toggle ${s.rotulo} indisponível (sem Rust IPC). Apenas re-sonda portas.`
                        : `${s.rotulo} · ${s.online ? "Clique para parar" : "Clique para iniciar"}`
                    }
                  >
                    <div className="flex items-center gap-1.5 w-full">
                      <CirculoStatus online={s.online} />
                      <span className="text-[11.5px] font-medium truncate">{s.rotulo}</span>
                      {busyEnergia === s.nome && (
                        <span className="ml-auto inline-block h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                      )}
                    </div>
                    <div className="text-[10px] text-muted/90 truncate w-full leading-tight">
                      {sublinha}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Status transição energia / feedback */}
            {(busyEnergia === "start_all" || busyEnergia === "stop_all" || !!feedback || !tauri.isTauri) && (
              <div className={"mt-2 space-y-1.5"}>
                {(busyEnergia === "start_all" || busyEnergia === "stop_all") && (
                  <div className={
                    "rounded-md px-2.5 py-1.5 text-[10.5px] leading-snug border " +
                    (busyEnergia === "start_all"
                      ? "bg-accent/10 border-accent/40 text-accent"
                      : "bg-danger/10 border-danger/40 text-danger")
                  }>
                    {busyEnergia === "start_all"
                      ? "▶ Ligando serviços em 3 etapas (Ollama → API :8000 → Frontend :3000)… atualizações em breve."
                      : "🛑 Parando serviços (Ollama vivo)… garante zero órfãos em ≤8s."}
                  </div>
                )}
                {feedback && (
                  <div className={
                    "rounded-md px-2.5 py-1.5 text-[10.5px] leading-snug border " +
                    (feedback.tipo === "ok"
                      ? "bg-success/10 border-success/40 text-success"
                      : feedback.tipo === "erro"
                        ? "bg-danger/10 border-danger/40 text-danger"
                        : "bg-bg3 border-border1 text-muted")
                  }>
                    {feedback.tipo === "ok" ? "✅ " : feedback.tipo === "erro" ? "⚠️ " : "ℹ️ "}
                    {feedback.msg}
                  </div>
                )}
                {!tauri.isTauri && !feedback && (
                  <div className="rounded-md px-2.5 py-1.5 text-[10.5px] leading-snug border border-amber-400/30 bg-amber-400/5 text-amber-300">
                    ⚠️ Modo navegador. Use o atalho "NeuroCore Launcher.lnk"
                    da Área de Trabalho para habilitar Ligar/Desligar.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navegação */}
          <nav className="px-2 py-3 flex flex-col gap-1 shrink-0">
            {NAV_ITENS.map((m) => {
              const ativo =
                (m.rota === "/" && pathname === "/") ||
                (m.rota !== "/" && pathname?.startsWith(m.rota));
              return (
                <Link key={m.id} href={m.rota} prefetch={false}>
                  <div
                    className={
                      "h-9 w-full px-3 rounded-md flex items-center gap-3 transition " +
                      (ativo
                        ? "bg-bg3 text-foreground border border-border1"
                        : "text-muted hover:bg-bg2 hover:text-foreground border border-transparent")
                    }
                  >
                    <span className="text-base">{m.ico}</span>
                    <span className="text-[13px] font-medium">{m.nome}</span>
                  </div>
                </Link>
              );
            })}
          </nav>

          <div className="h-px bg-border1 mx-3 my-1 shrink-0" />

          {/* Atalhos */}
          <div className="px-4 pt-2 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted shrink-0">
            Atalhos
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1 min-h-0">
            {[
              { k: "chat",     nome: "💬 Abrir Chat Web",       hint: "localhost:3000/chat" },
              { k: "swagger",  nome: "📄 Swagger API /docs",    hint: ":8000/docs" },
              { k: "tags",     nome: "🧠 Ollama modelos",       hint: ":11434" },
              { k: "memoria",  nome: "🗂️ Abrir memória G:",     hint: "G:\\memory" },
              { k: "projeto",  nome: "📂 Abrir pasta projeto",  hint: "NeuroCore\\" },
            ].map((a) => (
              <button
                key={a.k}
                onClick={() => abrirAtalho(a.k as any)}
                className="h-10 w-full rounded-md px-3 text-left flex flex-col justify-center hover:bg-bg2 border border-transparent transition"
                title={a.hint}
              >
                <div className="text-[12.5px] font-medium">{a.nome}</div>
                <div className="text-[10.5px] text-muted">{a.hint}</div>
              </button>
            ))}
          </div>

          {/* Rodape sidebar · Config Launcher */}
          <div className="border-t border-border1 px-3 py-2 text-[10.5px] text-muted shrink-0 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-semibold">NeuroCore · v0.1</div>
                <div className="text-muted/80" suppressHydrationWarning>
                  Modo:{" "}
                  {!tauri.ready
                    ? "…"
                    : tauri.isTauri
                      ? "Launcher Desktop"
                      : "Navegador Web"}
                </div>
              </div>
              <CirculoStatus online={tauri.ready && tauri.isTauri} suppressHydrationWarning />
            </div>
            <label className="flex items-center justify-between gap-2 cursor-pointer group">
              <span className="truncate text-muted group-hover:text-foreground transition">
                Manter Ollama vivo ao sair
              </span>
              <input type="checkbox"
                checked={lc.cfg.manter_ollama_vivo_ao_sair}
                onChange={(e) => lc.atualizar({ manter_ollama_vivo_ao_sair: e.target.checked })}
                className="h-3.5 w-3.5 accent-accent" />
            </label>
            <label className="flex items-center justify-between gap-2 cursor-pointer group">
              <span className="truncate text-muted group-hover:text-foreground transition">
                Chat abre no WebView interno
              </span>
              <input type="checkbox"
                checked={lc.cfg.abrir_chat_em_webview}
                onChange={(e) => lc.atualizar({ abrir_chat_em_webview: e.target.checked })}
                className="h-3.5 w-3.5 accent-accent" />
            </label>
            <label className="flex items-center justify-between gap-2 cursor-pointer group">
              <span className="truncate text-muted group-hover:text-foreground transition">
                Poll a cada
              </span>
              <select value={String(lc.cfg.poll_interval_ms)}
                      onChange={(e) => lc.atualizar({ poll_interval_ms: Number(e.target.value) })}
                      className="h-6 px-1.5 rounded bg-bg2 border border-border1 text-[10.5px] outline-none focus:border-accent/60">
                <option value="2000">2s (rápido)</option>
                <option value="4000">4s (padrão)</option>
                <option value="8000">8s</option>
                <option value="15000">15s (econômico)</option>
              </select>
            </label>
          </div>
        </aside>

        {/* COLUNA 2 · CENTRO */}
        <main className="h-full w-full flex flex-col bg-bg0 overflow-hidden min-w-0" suppressHydrationWarning>
          {children}
        </main>

        {/* COLUNA 3 · PAINEL DIREITO REUTILIZAVEL */}
        <PainelDireito pollMs={2500} />
      </div>
    </div>
  );
}
