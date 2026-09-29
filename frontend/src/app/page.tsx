"use client";

import React, { useMemo, useState } from "react";
import { usePainelStatus } from "../components/use_painel_status";
import { useTauriEnv } from "../components/use_tauri_env";
import {
  CirculoStatus,
  Card,
  formatarUptime,
} from "../components/ui_utils";
import type { StatusServico } from "../components/types";

export default function DashboardPage() {
  const ps = usePainelStatus(2500);
  const tauri = useTauriEnv();
  const [busy, setBusy] = useState<null | "start_all" | "stop_all">(null);
  const [feedback, setFeedback] = useState<{ tipo: "ok" | "erro"; msg: string } | null>(null);

  const {
    erro,
    tentativasFalhas,
    habilidades,
    feitos,
    xpTotal,
    nivelGlobal,
    xpParaProx,
    painel,
  } = ps;

  const servicos: StatusServico[] = useMemo(() => {
    const apiUp = !erro && !!painel;
    const ollamaUp = painel ? painel.vram.online : tentativasFalhas < 3;
    const frontUp = !!painel;
    return [
      { nome: "ollama", rotulo: "Ollama (Modelos)", icone: "🧠", online: ollamaUp, porta: 11434, uptime_segundos: painel?.uptime_segundos ? Math.floor(painel.uptime_segundos * 1.1) : undefined },
      { nome: "api", rotulo: "API Prometeu FastAPI", icone: "🔌", online: apiUp, porta: 8000, uptime_segundos: painel?.uptime_segundos },
      { nome: "frontend", rotulo: "Next.js Frontend", icone: "🎨", online: frontUp, porta: 3000 },
      { nome: "chatcli", rotulo: "Chat CLI Python", icone: "⌨️", online: false },
    ];
  }, [erro, painel, tentativasFalhas]);

  async function ligarRapido() {
    if (busy) return;
    setBusy("start_all");
    setFeedback(null);
    if (!tauri.isTauri) {
      setFeedback({
        tipo: "erro",
        msg:
          "⚠️ Modo navegador: Ligar Tudo depende do Tauri Desktop. Para habilitar clique 2x no atalho 'NeuroCore Launcher.lnk' da Área de Trabalho. Enquanto isso, inicie manualmente: .venv\\Scripts\\python.exe -m uvicorn core.api:app --port 8000 · ollama serve · cd frontend && npm run dev.",
      });
      // Re-sonda para pegar serviços que já estão rodando de sessões anteriores (contexto TRAE):
      try {
        const [o, a, f] = await Promise.allSettled([
          fetch("http://127.0.0.1:11434/api/tags", { method: "HEAD" }).then((r) => r.ok),
          fetch("http://127.0.0.1:8000/api/status", { cache: "no-store" }).then((r) => r.ok),
          fetch("http://localhost:3000/", { method: "HEAD" }).then((r) => r.ok),
        ]);
        const on = [o, a, f].filter((x) => x.status === "fulfilled" && (x as any).value).length;
        setFeedback({
          tipo: "ok",
          msg:
            `ℹ️ Sondagem concluída. ${on} de 3 serviços estão online (portas 11434 / 8000 / 3000). Use os scripts PowerShell para iniciar os que faltam.`,
        });
        setTimeout(() => ps.carregar(true), 1800);
      } catch {}
      setTimeout(() => setBusy(null), 300);
      setTimeout(() => setFeedback(null), 16000);
      return;
    }
    try {
      const ret = await tauri.invoke<string>("start_all", { include_ollama: true });
      setFeedback({ tipo: "ok", msg: ret || "Serviços iniciados. Aguarde subida em cascata (Ollama → API → Front)." });
      setTimeout(() => ps.carregar(true), 2000);
    } catch (e: any) {
      console.error("Ligar tudo falhou:", e);
      setFeedback({ tipo: "erro", msg: e?.message || e?.toString() || "Falha ao ligar serviços (veja console)." });
    } finally {
      setTimeout(() => setBusy(null), 300);
      setTimeout(() => setFeedback(null), 9000);
    }
  }

  async function desligarRapido() {
    if (busy) return;
    setBusy("stop_all");
    setFeedback(null);
    if (!tauri.isTauri) {
      setFeedback({
        tipo: "erro",
        msg:
          "⚠️ Modo navegador: Desligar Tudo requer Launcher Desktop. Use scripts\\parar_prometeu.ps1 ou feche os terminais diretamente. Re-sondando portas...",
      });
      for (let i = 0; i < 3; i++) {
        await new Promise((r) => setTimeout(r, i === 0 ? 1200 : 4000));
        ps.carregar(true);
      }
      setTimeout(() => setBusy(null), 300);
      setTimeout(() => setFeedback(null), 16000);
      return;
    }
    try {
      const ret = await tauri.invoke<string>("stop_all", { include_ollama: false });
      setFeedback({ tipo: "ok", msg: ret || "Desligamento em andamento (Ollama permanecerá vivo)." });
      setTimeout(() => ps.carregar(true), 3000);
    } catch (e: any) {
      console.error("Desligar tudo falhou:", e);
      setFeedback({ tipo: "erro", msg: e?.message || e?.toString() || "Falha ao desligar serviços (veja console)." });
    } finally {
      setTimeout(() => setBusy(null), 300);
      setTimeout(() => setFeedback(null), 9000);
    }
  }

  async function testarPrompt(tag: "codigo" | "so" | "geral") {
    const mapa = {
      codigo:  "Crie uma função Python curta que calcula fibonacci(n).",
      so:      "abre bloco de notas.",
      geral:   "Oi Prometeu, tudo bem com você hoje? Fale um pouco do seu estado.",
    } as const;
    try {
      await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem: mapa[tag], sessao_id: `launcher_dash_${tag}_${Date.now()}` }),
      });
      setTimeout(() => ps.carregar(true), 1500);
    } catch {}
  }

  return (
    <div className="h-full w-full overflow-y-auto px-6 py-5 space-y-5" suppressHydrationWarning>
      {/* Hero boas-vindas */}
      <div className="rounded-2xl border border-border1 bg-gradient-to-br from-bg1 to-bg0 p-6 shadow-glow/60" suppressHydrationWarning>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted font-semibold">
              <span className="inline-block h-2 w-2 rounded-full bg-accent animate-pulse" />
              NeuroCore · Launcher Desktop
            </div>
            <h1 className="mt-1 text-[26px] font-bold leading-tight text-foreground">
              Olá, Jhon! 👋 Bem-vindo de volta ao seu <span className="text-accent">cérebro local</span>.
            </h1>
            <p className="mt-2 text-[13px] text-muted max-w-2xl">
              Aqui você liga, desliga, monitora e conversa com o Prometeu sem precisar abrir terminal.
              Nível global <b className="text-accent"> LVL {nivelGlobal}</b> · {xpTotal} XP · Falta{" "}
              <b>{Math.max(0, xpParaProx - xpTotal)}</b> XP para o próximo nível.
            </p>
          </div>
          <div className="flex flex-col gap-2 shrink-0 w-[260px]">
            <button
              onClick={ligarRapido}
              disabled={!!busy}
              title={
                busy === "start_all"
                  ? "Iniciando serviços…"
                  : !tauri.isTauri
                    ? "Modo navegador: apenas re-sonda as portas (sem Rust IPC). Ligar serviços reais via PowerShell ou abra o atalho Launcher Desktop."
                    : "▶️ Ligar Tudo: Ollama → API Prometeu → Next.js"
              }
              className={
                "h-10 rounded-lg font-bold text-[13px] transition shadow-glow disabled:opacity-60 disabled:cursor-not-allowed " +
                (tauri.isTauri
                  ? "bg-accent text-bg0 hover:brightness-110"
                  : "bg-bg2 text-muted border border-border1 hover:border-accent/40 hover:text-foreground cursor-pointer")
              }
            >
              {busy === "start_all" ? "⏳ Ligando serviços…" : "▶️ Ligar Tudo (3 serviços)"}
            </button>
            <button
              onClick={desligarRapido}
              disabled={!!busy}
              title={
                busy === "stop_all"
                  ? "Desligando serviços…"
                  : !tauri.isTauri
                    ? "Modo navegador: apenas re-sonda. Para desligar serviços reais use scripts/parar_prometeu.ps1 ou feche os terminais."
                    : "🛑 Desligar API + Frontend (mantém Ollama vivo por padrão)"
              }
              className={
                "h-9 rounded-lg border text-[12px] font-semibold transition disabled:opacity-60 disabled:cursor-not-allowed " +
                (tauri.isTauri
                  ? "bg-bg2 border-danger/40 text-danger hover:bg-danger/10"
                  : "bg-bg2 border-border1 text-muted hover:border-danger/30 hover:text-danger cursor-pointer")
              }
            >
              {busy === "stop_all" ? "⏳ Desligando serviços…" : "🛑 Desligar Tudo (mantém Ollama)"}
            </button>
            {feedback && (
              <div
                className={
                  "rounded-md px-3 py-2 text-[11px] leading-snug border " +
                  (feedback.tipo === "ok"
                    ? "bg-success/10 border-success/40 text-success"
                    : "bg-danger/10 border-danger/40 text-danger")
                }
              >
                {feedback.tipo === "ok" ? "✅ " : "⚠️ "}
                {feedback.msg}
              </div>
            )}
            {!tauri.isTauri && (
              <div className="rounded-md border border-amber-400/30 bg-amber-400/5 text-[11px] text-amber-300 px-3 py-2 leading-snug">
                ⚠️ Ambiente navegador detectado. Botões de energia funcionam 100%
                somente no Launcher Desktop Tauri. Abra pelo atalho "NeuroCore
                Launcher.lnk" na sua Área de Trabalho.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4 serviços */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-[12px] font-semibold uppercase tracking-wider text-muted">
            Status dos Serviços
          </h2>
          <span className="text-[11px] text-muted">
            {servicos.filter((x) => x.online).length} / {servicos.length} online
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {servicos.map((s) => (
            <Card
              key={s.nome}
              icon={s.icone}
              title={s.rotulo}
              right={
                <span className="flex items-center gap-1.5 text-[11px]">
                  <CirculoStatus online={s.online} />
                  <span className={s.online ? "text-success" : "text-muted"}>
                    {s.online ? "Online" : "Offline"}
                  </span>
                </span>
              }
            >
              <div className="text-[11.5px] text-muted font-mono mt-1 space-y-0.5">
                {s.porta && <div>Porta: <span className="text-foreground">:{s.porta}</span></div>}
                {s.uptime_segundos && (
                  <div>Uptime: <span className="text-foreground">{formatarUptime(s.uptime_segundos)}</span></div>
                )}
                {s.nome === "api" && painel?.router && (
                  <div>
                    Router: <span className="text-accent font-semibold">
                      {painel.router.modo_force_local ? "FORCE LOCAL" : "HÍBRIDO"}
                    </span>
                  </div>
                )}
                {s.nome === "ollama" && painel?.vram && (
                  <div>VRAM: <span className="text-foreground">{painel.vram.resumo}</span></div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Ações rápidas de teste */}
      <section>
        <h2 className="text-[12px] font-semibold uppercase tracking-wider text-muted mb-2">
          Ações Rápidas · Testar Habilidades
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { id: "geral",  nome: "🧠 Geral",     desc: "Pergunta de apresentação ao cortex_geral.", btn: "Enviar ping geral" },
            { id: "codigo", nome: "⚡ Código",    desc: "Prompt para o especialista llm_code.",   btn: "Gerar Fibonacci Python" },
            { id: "so",     nome: "🖥️ Sistema",  desc: "Abre bloco de notas via os_control.",    btn: "Abrir bloco de notas" },
          ].map((t) => (
            <Card key={t.id} icon={t.nome.split(" ")[0]} title={t.nome.split(" ").slice(1).join(" ")}>
              <p className="text-[12px] text-muted mb-3 min-h-[32px]">{t.desc}</p>
              <button
                onClick={() => testarPrompt(t.id as any)}
                className="h-8 w-full rounded-md bg-bg3 hover:bg-accent hover:text-bg0 border border-border1 hover:border-accent transition text-[12px] font-semibold"
              >
                ▶ {t.btn}
              </button>
            </Card>
          ))}
        </div>
      </section>

      {/* Habilidades + Feitos (resumo) */}
      <section className="grid grid-cols-1 lg:grid-cols-5 gap-3">
        <div className="lg:col-span-3 space-y-3">
          <Card icon="🧬" title="7 Habilidades · Visão Geral" right={<span className="text-[10px] text-muted">Soma XP: {xpTotal}</span>}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {habilidades.map((h) => (
                <div key={h.id} className="rounded-md bg-bg2 border border-border1 px-3 py-2 flex items-center gap-2">
                  <span className="text-[16px]">{h.icone}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between text-[12px]">
                      <span className="font-semibold truncate">{h.nome}</span>
                      <span className="font-mono text-[10px] text-muted">
                        {h.xp}/{h.xp_para_prox} XP · LVL {h.nivel}
                      </span>
                    </div>
                    <div className="h-1 mt-1 rounded-full bg-bg3 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-accent"
                        style={{ width: `${Math.min(100, Math.max(0, Math.round((h.xp / Math.max(1, h.xp_para_prox)) * 100)))}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-3">
          <Card icon="🏆" title="Wall of Wins · Últimos feitos" right={<span className="text-[10px] text-accent font-bold">{feitos.length} conquistas</span>}>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {feitos.slice(0, 6).map((f) => (
                <div key={f.id} className="flex items-start gap-2">
                  <div className="text-[15px] mt-0.5">{f.emoji}</div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] font-semibold leading-tight">{f.nome}</div>
                    <div className="text-[10.5px] text-muted">{f.descricao}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card icon="🛡️" title="Híbrido · Segurança">
            <ul className="text-[11.5px] text-muted space-y-1.5 leading-snug">
              <li>• 100% <b className="text-foreground">Local</b> · nada sai pro seu PC sem permissão.</li>
              <li>• Router: <b className="text-accent">{(painel?.router?.modo_force_local ?? true) ? "FORCE LOCAL" : "Híbrido"}</b> · teto R$ <b>0,00</b>/mês.</li>
              <li>• OS Control: apenas <b>whitelist</b> de programas & pastas permitidos.</li>
              <li>• Docs estratégicos do NeuroCore ficam em <b>docs/ · LOCAL ONLY</b> (.gitignore).</li>
            </ul>
          </Card>
        </div>
      </section>
    </div>
  );
}
