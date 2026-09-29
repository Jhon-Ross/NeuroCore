"use client";

// ================================================================
// PÁGINA /chat — Mantem o CHAT REAL original do Prometeu,
// mas agora renderiza DENTRO do LauncherShell (sem colunas duplicadas).
// Colunas sidebar e painel direito ja vem de app/layout.tsx.
// ================================================================

import React, { useEffect, useMemo, useRef, useState } from "react";
import { usePainelStatus, API_BASE } from "../../components/use_painel_status";
import type { MensagemChat, HabilidadeUI } from "../../components/types";

export default function ChatPage() {
  const ps = usePainelStatus(10000);
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [textoInput, setTextoInput] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const habilidades: HabilidadeUI[] = useMemo(() => {
    const arr = ps.painel?.rpg?.habilidades?.length ? ps.painel.rpg.habilidades : [];
    return arr.map((h, idx) => ({ ...h, ativo: idx === 0 ? true : (h.ativo ?? (h.nivel > 0 || h.xp > 0)) }));
  }, [ps.painel]);
  const modeloAtivo = ps.painel?.especialistas?.llm_core?.modelo ?? "llama3:latest";

  // Scroll automatico quando chegam msgs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [mensagens]);

  // Auto-resize textarea
  useEffect(() => {
    const t = textareaRef.current;
    if (!t) return;
    t.style.height = "auto";
    t.style.height = Math.min(140, t.scrollHeight) + "px";
  }, [textoInput]);

  async function enviarMensagem() {
    const txt = textoInput.trim();
    if (!txt || enviando) return;
    const idUser = `u-${Date.now()}`;
    setMensagens((m) => [...m, { id: idUser, role: "user", content: txt, timestamp: Date.now() }]);
    setTextoInput("");
    setEnviando(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 240_000);
    try {
      const body: any = { mensagem: txt, habilidade_alvo: "auto" };
      if (typeof sessionId === "number" && sessionId > 0) body.session_id = sessionId;
      const r = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      if (typeof j.session_id === "number" && j.session_id > 0) setSessionId(j.session_id);
      setMensagens((m) => [...m, {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: String(j.resposta_texto ?? "⚠️ Sem resposta."),
        tempo_ms: Number(j.tempo_total_ms ?? 0),
        modelo: j.modelo_usado ?? undefined,
        tokens: Number(j.tokens_usados ?? 0),
        xp: Number(j.xp_ganho ?? 0),
        timestamp: Date.now(),
      }]);
      setTimeout(() => ps.carregar(true), 250);
    } catch (e) {
      const err = e instanceof Error ? (e.name === "AbortError" ? "Timeout após 3min" : e.message) : "erro";
      setMensagens((m) => [...m, {
        id: `a-${Date.now()}`, role: "assistant",
        content: "⚠️ **Erro ao enviar.** Verifique a API :8000. Detalhe: " + err,
        timestamp: Date.now(),
      }]);
    } finally {
      clearTimeout(timeoutId);
      setEnviando(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }

  return (
    <div className="h-full w-full flex flex-col bg-bg0" suppressHydrationWarning>
      {/* Barra de topo */}
      <div className="h-14 px-6 flex items-center justify-between border-b border-border1 bg-bg1/40 backdrop-blur shrink-0" suppressHydrationWarning>
        <div className="min-w-0">
          <div className="text-[15px] font-bold truncate">
            Prometeu · Sessão Chat {typeof sessionId === "number" ? `#${sessionId}` : "Nova"}
          </div>
          <div className="text-[11px] text-muted -mt-0.5 truncate">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-success mr-1.5 align-middle" />
            Córtex Geral · {modeloAtivo} · RX 7600 8GB · Local 100%
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="h-8 px-3 rounded-md bg-bg2 border border-border1 text-[11px] text-muted grid place-items-center">
            Modelo: <span className="text-foreground ml-1 font-mono truncate max-w-[200px]">{modeloAtivo}</span>
          </div>
          <div className={`h-8 px-3 rounded-md border text-[11px] grid place-items-center font-semibold ${
            (ps.painel?.router?.modo_force_local ?? true)
              ? "bg-accent-soft border-accent/40 text-accent"
              : "bg-bg2 border-border1 text-foreground"
          }`}>
            {(ps.painel?.router?.modo_force_local ?? true) ? "FORCE LOCAL" : "HÍBRIDO"}
          </div>
        </div>
      </div>

      {/* Área de mensagens */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6 flex flex-col justify-start gap-5 min-h-0">
        {mensagens.length === 0 ? (
          <div className="mx-auto max-w-3xl w-full rounded-xl border border-border1 bg-bg1 px-8 py-10 text-center shadow-glow mt-auto mb-auto">
            <div className="text-4xl mb-3">🧠✨</div>
            <div className="text-[20px] font-bold text-accent mb-2">Prometeu está conectado!</div>
            <div className="text-muted text-[13px] max-w-xl mx-auto leading-relaxed">
              Escreva algo abaixo para começar. Tente um dos exemplos:
            </div>
            <div className="mt-6 flex flex-wrap justify-center gap-2 text-[12px]">
              {[
                "Oi Prometeu, tudo bem?",
                "Crie uma função Python fatorial(n) recursiva",
                "abre a calculadora",
                "Quais minhas habilidades e níveis?",
              ].map((ex) => (
                <button key={ex}
                  onClick={() => setTextoInput(ex)}
                  className="px-3 py-2 rounded-lg bg-bg2 border border-border1 text-foreground hover:bg-bg3 hover:border-accent/50 transition">
                  {ex}
                </button>
              ))}
            </div>
            {ps.erro && ps.apiOnline === false && (
              <div className="mt-4 text-[12px] rounded-md border border-danger/50 bg-danger/10 text-danger px-4 py-2 inline-block">
                ⚠️ API :8000 offline: {ps.erro}
              </div>
            )}
          </div>
        ) : (
          mensagens.map((m) => (
            <div key={m.id} className={`w-full flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-5 py-3 border whitespace-pre-wrap break-words shadow ${
                m.role === "user"
                  ? "bg-accent/95 text-bg0 border-accent rounded-br-sm"
                  : "bg-bg1 text-foreground border-border1 rounded-bl-sm"
              }`}>
                <div className="text-[13.5px] leading-relaxed">{m.content}</div>
                {m.role === "assistant" && (
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10.5px] opacity-85">
                    {typeof m.tempo_ms === "number" && <span>⏱️ {Math.round(m.tempo_ms)}ms</span>}
                    {typeof m.tokens === "number" && m.tokens > 0 && <span>🎟️ {m.tokens} tokens</span>}
                    {m.modelo && <span className="font-mono">🤖 {m.modelo}</span>}
                    {typeof m.xp === "number" && m.xp > 0 && <span className="font-bold text-accent">✨ +{m.xp} XP</span>}
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

      {/* Input */}
      <div className="h-auto min-h-[112px] px-8 pb-5 pt-3 border-t border-border1 bg-bg1/40 shrink-0">
        <div className="mx-auto max-w-3xl w-full grid grid-cols-[1fr_auto] gap-3">
          <textarea
            ref={textareaRef}
            value={textoInput}
            onChange={(e) => setTextoInput(e.target.value)}
            onKeyDown={(ev) => {
              if (ev.key === "Enter" && !ev.shiftKey && !ev.nativeEvent.isComposing) {
                ev.preventDefault();
                enviarMensagem();
              }
            }}
            placeholder="Digite algo para o Prometeu… (Enter envia, Shift+Enter nova linha)"
            disabled={enviando || ps.apiOnline === false}
            rows={2}
            className="min-h-[64px] max-h-[140px] w-full resize-none rounded-xl bg-bg2 border border-border1 px-4 py-3
                       text-[13px] text-foreground placeholder:text-muted/60 outline-none
                       focus:ring-2 focus:ring-accent/40 focus:border-accent/60
                       disabled:opacity-50"
          />
          <button
            onClick={enviarMensagem}
            disabled={enviando || !textoInput.trim() || ps.apiOnline === false}
            title={ps.apiOnline === false ? "API :8000 offline — não é possível enviar" : enviando ? "Enviando…" : "Enviar mensagem"}
            className="h-auto self-stretch px-5 rounded-xl bg-accent text-bg0 font-bold text-[13px]
                       disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110 transition grid place-items-center">
            {enviando ? "…" : ps.apiOnline === false ? "🔴" : "↵ Enviar"}
          </button>
        </div>
        <div className="mx-auto max-w-3xl w-full mt-2 text-[10.5px] text-muted flex items-center justify-between">
          <div>
            API FastAPI:
            <span className={`ml-1.5 font-mono ${ps.apiOnline === false ? "text-danger" : "text-success"} font-bold`}>
              {ps.apiOnline === false
                ? "OFFLINE"
                : ps.apiOnline === null
                  ? "…"
                  : "http://127.0.0.1:8000"}
            </span>
            {typeof sessionId === "number" && <span className="ml-3">Sessão SQLite: <span className="font-mono">#{sessionId}</span></span>}
          </div>
          <div>Respostas 100% locais · nada sai do seu PC</div>
        </div>
      </div>
    </div>
  );
}
