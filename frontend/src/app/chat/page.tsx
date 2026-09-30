"use client";

// ================================================================
// PÁGINA /chat — Chat completo do Prometeu com Histórico de Sessões.
// Layout: sidebar de histórico (esquerda) + área de chat (direita).
// Paleta oficial: PRETO #07070A + ÂMBAR #F59E0B.
// ================================================================

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePainelStatus, API_BASE } from "../../components/use_painel_status";
import type { MensagemChat, ProviderValor, ProviderOpcaoUI } from "../../components/types";
import { CodeBlockRunner } from "../../components/CodeBlockRunner";
import { ChatHistorySidebar } from "../../components/ChatHistorySidebar";

function ConteudoMensagem({ content, onXpGanho }: { content: string; onXpGanho?: (xp: number) => void }) {
  const parts = useMemo(() => {
    const regex = /```([a-zA-Z0-9_\-\+]*)\s*\n([\s\S]*?)```/g;
    const res: { type: "text" | "code"; content: string; language?: string }[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        res.push({
          type: "text",
          content: content.slice(lastIndex, match.index),
        });
      }
      res.push({
        type: "code",
        language: match[1] || "python",
        content: match[2].trimEnd(),
      });
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < content.length) {
      res.push({
        type: "text",
        content: content.slice(lastIndex),
      });
    }

    return res;
  }, [content]);

  return (
    <div className="text-[13.5px] leading-relaxed">
      {parts.map((p, idx) => {
        if (p.type === "code") {
          return (
            <CodeBlockRunner
              key={idx}
              code={p.content}
              language={p.language}
              onXpGanho={onXpGanho}
            />
          );
        }
        return (
          <span key={idx} className="whitespace-pre-wrap">
            {p.content}
          </span>
        );
      })}
    </div>
  );
}

export default function ChatPage() {
  const ps = usePainelStatus(10000);
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [textoInput, setTextoInput] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sidebarAberta, setSidebarAberta] = useState(true);
  const [recarregarHistorico, setRecarregarHistorico] = useState(0);
  const [carregandoSessao, setCarregandoSessao] = useState(false);

  // Estado do provider selecionado no dropdown. Padrão = "auto" (Prometeu decide).
  const [providerSelecionado, setProviderSelecionado] = useState<ProviderValor>("auto");

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modeloAtivo = ps.painel?.especialistas?.llm_core?.modelo ?? "llama3:latest";

  // Carrega mensagens de uma sessão existente do SQLite
  const carregarSessao = useCallback(async (id: number) => {
    setCarregandoSessao(true);
    setSessionId(id);
    setMensagens([]);
    try {
      const r = await fetch(`${API_BASE}/api/chat/sessions/${id}/messages?limite=100`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const dados = await r.json();
      const msgs: MensagemChat[] = (dados.mensagens ?? []).map((m: { id: number; role: string; content: string; timestamp_iso: string }) => ({
        id: `hist-${m.id}`,
        role: m.role as "user" | "assistant",
        content: m.content,
        timestamp: new Date(m.timestamp_iso?.replace(" ", "T") + "Z").getTime() || Date.now(),
      }));
      setMensagens(msgs);
    } catch {
      setMensagens([{ id: `err-${Date.now()}`, role: "assistant", content: "⚠️ Não foi possível carregar o histórico desta sessão.", timestamp: Date.now() }]);
    } finally {
      setCarregandoSessao(false);
    }
  }, []);

  // Nova conversa: limpa estado
  const iniciarNovaSessao = useCallback(() => {
    setSessionId(null);
    setMensagens([]);
    setTextoInput("");
  }, []);

  // ================================================================
  // LISTA DE PROVIDERS DO DROPDOWN
  // Prioridade: (a) usa a lista vinda do backend (GET /api/status → providers_disponiveis)
  //             que já vem com `disponivel` calculado. (b) Fallback hardcoded se
  //             a API ainda não respondeu a primeira vez, para UI nunca ficar vazia.
  // ================================================================
  const providersDropdown: ProviderOpcaoUI[] = useMemo<ProviderOpcaoUI[]>(() => {
    if (Array.isArray(ps.painel?.providers_disponiveis) && ps.painel.providers_disponiveis.length > 0) {
      return ps.painel.providers_disponiveis as ProviderOpcaoUI[];
    }
    // Fallback offline (API :8000 ainda não deu a primeira resposta).
    // IMPORTANTE: NÃO marcamos como disponivel=false, pois mentiríamos pro usuário
    // dizendo que "falta chave" quando na verdade ele ainda não sabe. Usamos
    // undefined e mostramos "(⏳ aguardando API...)" no label do option.
    return [
      { valor: "auto", label: "🔮 Automático (Prometeu decide)", descricao: "O Prometeu escolhe: Ollama para conversa casual, Anthropic para código avançado.", custo_nominal_brl: 0, requer_chave: false, disponivel: true },
      { valor: "local", label: "🧠 Ollama RX 7600 (Local)", descricao: "100% na sua GPU AMD. R$0,00. Privacidade máxima.", custo_nominal_brl: 0, requer_chave: false, disponivel: true },
      { valor: "anthropic", label: "✨ Anthropic Claude Direto", descricao: "Melhor raciocínio técnico hoje. Custo ~R$0.03~R$0.30/resp.", custo_nominal_brl: 0.03, requer_chave: true, env_var: "ANTHROPIC_API_KEY", disponivel: undefined, motivo_indisponivel: "API :8000 ainda não inicializada; aguarde a primeira resposta do /api/status." },
      { valor: "openrouter", label: "🌐 OpenRouter Agregador", descricao: "1 chave = GPT-4o, Claude, Gemini, Llama Cloud etc.", custo_nominal_brl: 0.03, requer_chave: true, env_var: "OPENROUTER_API_KEY", disponivel: undefined, motivo_indisponivel: "API :8000 ainda não inicializada; aguarde a primeira resposta do /api/status." },
      { valor: "gemini", label: "🪄 Google Gemini Direto", descricao: "Bom balanço custo × qualidade.", custo_nominal_brl: 0.01, requer_chave: true, env_var: "GEMINI_API_KEY", disponivel: undefined, motivo_indisponivel: "API :8000 ainda não inicializada; aguarde a primeira resposta do /api/status." },
    ];
  }, [ps.painel]);

  // Provider ATUALMENTE selecionado (para pegar label/descricao/disponivel/motivo_indisponivel)
  const providerAtual: ProviderOpcaoUI = useMemo(() => {
    return providersDropdown.find(p => p.valor === providerSelecionado) ?? providersDropdown[0];
  }, [providersDropdown, providerSelecionado]);

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
    setMensagens((m) => [...m, { id: idUser, role: "user", content: txt, timestamp: Date.now(), provedor: providerSelecionado }]);
    setTextoInput("");
    setEnviando(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 240_000);
    try {
      const body: Record<string, unknown> = {
        mensagem: txt,
        habilidade_alvo: "auto",
        provider: providerSelecionado,  // ← NOVO: passa o valor do dropdown para o backend
      };
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
        // 👇 NOVOS CAMPOS PROVIDER (vindos do backend via ChatResponse)
        provedor: String(j.roteamento_provedor ?? "").trim() || undefined,
        roteamento_motivo: String(j.roteamento_motivo ?? "").trim() || undefined,
        custo_estimado_reais: Number(j.custo_estimado_reais ?? 0) > 0 ? Number(j.custo_estimado_reais) : undefined,
        timestamp: Date.now(),
      }]);
      setTimeout(() => ps.carregar(true), 250);
      // Atualiza a lista de sessões na sidebar após cada mensagem
      setRecarregarHistorico((n) => n + 1);
    } catch (e) {
      const err = e instanceof Error ? (e.name === "AbortError" ? "Timeout após 4min (cold start HDD?)" : e.message) : "erro";
      setMensagens((m) => [...m, {
        id: `a-${Date.now()}`, role: "assistant",
        content: "⚠️ **Erro ao enviar.** Verifique a API :8000. Detalhe: " + err,
        timestamp: Date.now(),
        provedor: providerSelecionado,
      }]);
    } finally {
      clearTimeout(timeoutId);
      setEnviando(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }

  return (
    <div className="h-full w-full flex flex-row bg-bg0 overflow-hidden" suppressHydrationWarning>
      {/* ====== SIDEBAR DE HISTÓRICO ====== */}
      <div
        className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${
          sidebarAberta ? "w-[200px]" : "w-0"
        }`}
      >
        {sidebarAberta && (
          <ChatHistorySidebar
            sessionIdAtiva={sessionId}
            onSelecionarSessao={carregarSessao}
            onNovaSessao={iniciarNovaSessao}
            recarregarTrigger={recarregarHistorico}
          />
        )}
      </div>

      {/* ====== ÁREA PRINCIPAL DO CHAT ====== */}
      <div className="flex-1 flex flex-col min-w-0" suppressHydrationWarning>
      {/* Barra de topo */}
      <div className="h-auto px-4 py-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border1 bg-bg1/40 backdrop-blur shrink-0" suppressHydrationWarning>
        <div className="flex items-center gap-2 min-w-0">
          {/* Toggle sidebar */}
          <button
            onClick={() => setSidebarAberta((v) => !v)}
            title={sidebarAberta ? "Ocultar histórico" : "Mostrar histórico"}
            className="shrink-0 h-7 w-7 rounded-md border border-border1 bg-bg2 text-muted hover:text-foreground hover:border-accent/40 transition flex items-center justify-center text-[11px]"
          >
            {sidebarAberta ? "◀" : "▶"}
          </button>
          <div className="min-w-0">
            <div className="text-[14px] font-bold truncate">
              Prometeu {typeof sessionId === "number" ? `· Sessão #${sessionId}` : "· Nova Conversa"}
            </div>
            <div className="text-[11px] text-muted -mt-0.5 truncate">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-success mr-1.5 align-middle" />
              Córtex Geral · {modeloAtivo} · RX 7600 8GB · Local 100%
            </div>
          </div>
        </div>
        {/* --- NOVO BLOCO: CONTROLES DE PROVIDER --- */}
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          {/* (a) Dropdown de Seleção de Provider */}
          <div className="flex items-center gap-1.5">
            <label htmlFor="provider-select" className="text-[11px] text-muted">
              Inferência:
            </label>
            <select
              id="provider-select"
              value={providerSelecionado}
              onChange={(e) => setProviderSelecionado(e.target.value as ProviderValor)}
              disabled={enviando}
              title={providerAtual.descricao}
              className="h-9 px-3 pr-8 rounded-md bg-bg2 border border-border1 text-[12.5px] text-foreground
                         outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent/60
                         disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer appearance-none"
              style={{ backgroundImage: "linear-gradient(45deg, transparent 50%, #F59E0B 50%), linear-gradient(135deg, #F59E0B 50%, transparent 50%)", backgroundPosition: "calc(100% - 14px) calc(1em + 0px), calc(100% - 9px) calc(1em + 0px)", backgroundSize: "5px 5px, 5px 5px", backgroundRepeat: "no-repeat" }}
            >
              {providersDropdown.map((opt) => {
                // Label do option (texto VISÍVEL no dropdown aberto)
                // Regra:
                //   disponivel=true       → "(✅ pronto)"
                //   disponivel=false      → resumo do motivo_indisponivel se existir,
                //                           senão "(🔒 indisponível)"
                //   disponivel=undefined  → "(⏳ aguardando API...)"
                let sufixo = "";
                if (opt.requer_chave) {
                  if (opt.disponivel === true) {
                    sufixo = " (✅ pronto)";
                  } else if (opt.disponivel === false) {
                    const m = (opt.motivo_indisponivel ?? "").trim();
                    if (m) {
                      // Resumo: se for teto bloqueado + tem chave → mostra só "(🔒 teto R$0)" curto
                      //         se faltar chave → mostra só "(🔒 falta X)"
                      //         outros casos → "(🔒 indisponível)"
                      const temChave = m.includes("OK") || m.includes("ok");
                      const faltaChave = m.includes("NÃO configurada");
                      const temTeto = m.includes("TETO MENSAL BLOQUEADO") || m.includes("teto") || m.includes("Teto");
                      if (faltaChave && temTeto) {
                        sufixo = ` (🔒 falta ${opt.env_var ?? "chave"} + teto R$0)`;
                      } else if (faltaChave) {
                        sufixo = ` (🔒 falta ${opt.env_var ?? "chave"})`;
                      } else if (temTeto && temChave) {
                        sufixo = ` (🔒 teto R$0.00, 🔑 chave OK)`;
                      } else if (temTeto) {
                        sufixo = ` (🔒 teto bloqueado R$0.00)`;
                      } else {
                        sufixo = ` (🔒 indisponível)`;
                      }
                    } else {
                      sufixo = ` (🔒 falta ${opt.env_var ?? "chave"}/teto)`;
                    }
                  } else {
                    sufixo = " (⏳ aguardando API...)";
                  }
                }
                const titleFmt = `${opt.descricao}${opt.requer_chave ? ` | Requer chave: ${opt.env_var ?? ""}` : ""}${typeof opt.disponivel === "boolean" && !opt.disponivel ? ` | ⚠️ ${opt.motivo_indisponivel ?? "Indisponível"}` : ""}${opt.disponivel === undefined ? ` | ⏳ ${opt.motivo_indisponivel ?? "Aguardando primeira resposta da API :8000"}` : ""}`;
                return (
                  <option
                    key={opt.valor}
                    value={opt.valor}
                    title={titleFmt}
                  >
                    {opt.label}{sufixo}
                  </option>
                );
              })}
            </select>
          </div>

          {/* (b) Badge do Provider selecionado */}
          <div
            className={`h-8 px-3 rounded-md border text-[11px] grid place-items-center font-semibold whitespace-nowrap ${
              providerSelecionado === "local" || providerSelecionado === "auto"
                ? "bg-accent-soft border-accent/40 text-accent"
                : providerAtual.disponivel === true
                  ? "bg-bg2 border-border1 text-foreground"
                  : providerAtual.disponivel === false
                    ? "bg-danger/10 border-danger/40 text-danger"
                    : "bg-bg1 border-border1 text-muted" /* undefined = aguardando API */
            }`}
            title={
              providerAtual.disponivel === true
                ? providerAtual.descricao
                : providerAtual.disponivel === false
                  ? `Indisponível: ${providerAtual.motivo_indisponivel ?? "Configure a chave no .env e/ou aumente PROMETEU_TETO_MENSAL_REAIS > R$0,00"}`
                  : `Status desconhecido ainda: ${providerAtual.motivo_indisponivel ?? "Aguarde a API :8000 subir para receber a lista oficial de providers disponíveis."}`
            }
          >
            {providerSelecionado === "local"
              ? "LOCAL · R$0"
              : providerSelecionado === "auto"
                ? "AUTO · Decide sozinho"
                : providerAtual.disponivel === true
                  ? `${String(providerAtual.valor).toUpperCase()} · ~R$${providerAtual.custo_nominal_brl.toFixed(2)}`
                  : providerAtual.disponivel === false
                    ? `${String(providerSelecionado).toUpperCase()} · 🔒 INDISPONÍVEL`
                    : `${String(providerSelecionado).toUpperCase()} · ⏳ API OFFLINE`}
          </div>

          {/* (c) Badge FORCE LOCAL / HÍBRIDO antigo (mantido no canto) */}
          <div className={`h-8 px-3 rounded-md border text-[11px] grid place-items-center font-semibold whitespace-nowrap ${
            (ps.painel?.router?.modo_force_local ?? true)
              ? "bg-accent-soft border-accent/40 text-accent"
              : "bg-bg2 border-border1 text-foreground"
          }`}>
            {(ps.painel?.router?.modo_force_local ?? true) ? "FORCE LOCAL" : "HÍBRIDO"}
          </div>
        </div>
      </div>

      {/* Banner AVISO PROVIDER INDISPONÍVEL (só mostra se usuário escolheu um API e ele está 🔒) */}
      {providerSelecionado !== "local" && providerSelecionado !== "auto" && providerAtual.disponivel === false && (
        <div className="px-6 py-2 border-b border-danger/30 bg-danger/5 shrink-0">
          <div className="mx-auto max-w-3xl w-full text-[11.5px] text-danger flex items-start gap-2">
            <span className="mt-0.5">🔒</span>
            <div className="flex-1">
              <span className="font-bold">Provider <span className="uppercase">{providerSelecionado}</span> indisponível agora.</span>{" "}
              <span>{providerAtual.motivo_indisponivel ?? "Configure a chave no arquivo .env raiz e aumente PROMETEU_TETO_MENSAL_REAIS para algo maior que R$0,00."}</span>
              <span className="text-muted ml-1">Prometeu vai cair automaticamente para Ollama LOCAL (R$0,00) para não quebrar a conversa.</span>
            </div>
          </div>
        </div>
      )}
      {/* Banner AVISO PROVIDER STATUS DESCONHECIDO (aguardando API responder) */}
      {providerSelecionado !== "local" && providerSelecionado !== "auto" && providerAtual.disponivel === undefined && (
        <div className="px-6 py-2 border-b border-border1 bg-bg1/50 shrink-0">
          <div className="mx-auto max-w-3xl w-full text-[11.5px] text-muted flex items-start gap-2">
            <span className="mt-0.5">⏳</span>
            <div className="flex-1">
              <span className="font-bold">Aguardando API :8000 subir para confirmar disponibilidade do provider <span className="uppercase">{providerSelecionado}</span>.</span>{" "}
              <span>{providerAtual.motivo_indisponivel ?? "Clique em Ligar Tudo no Launcher para iniciar os serviços."}</span>
            </div>
          </div>
        </div>
      )}

      {/* Área de mensagens */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-5 flex flex-col justify-start gap-5 min-h-0">
        {carregandoSessao && (
          <div className="flex items-center justify-center py-8 gap-2 text-muted text-[12px]">
            <span className="h-2 w-2 rounded-full bg-accent animate-ping" />
            <span>Carregando histórico da sessão...</span>
          </div>
        )}
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
              <div className={`max-w-[85%] rounded-2xl px-5 py-3 border break-words shadow ${
                m.role === "user"
                  ? "bg-accent/95 text-bg0 border-accent rounded-br-sm whitespace-pre-wrap"
                  : "bg-bg1 text-foreground border-border1 rounded-bl-sm"
              }`}>
                {m.role === "user" ? (
                  <div className="text-[13.5px] leading-relaxed">{m.content}</div>
                ) : (
                  <ConteudoMensagem content={m.content} onXpGanho={() => ps.carregar(true)} />
                )}
                {m.role === "assistant" && (
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10.5px] opacity-90 items-center">
                    {typeof m.tempo_ms === "number" && <span>⏱️ {Math.round(m.tempo_ms)}ms</span>}
                    {typeof m.tokens === "number" && m.tokens > 0 && <span>🎟️ {m.tokens} tokens</span>}
                    {m.modelo && <span className="font-mono">🤖 {m.modelo}</span>}
                    {typeof m.xp === "number" && m.xp > 0 && <span className="font-bold text-accent">✨ +{m.xp} XP</span>}

                    {/* ======= NOVOS CAMPOS PROVIDER ======= */}
                    {m.provedor && (
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded-sm border ${
                          m.provedor === "ollama"
                            ? "border-accent/40 bg-accent/10 text-accent"
                            : "border-border1 bg-bg2 text-foreground"
                        }`}
                        title={m.roteamento_motivo ?? ""}
                      >
                        {m.provedor === "ollama" && "🧠 "}
                        {m.provedor === "anthropic" && "✨ "}
                        {m.provedor === "openrouter" && "🌐 "}
                        {m.provedor === "gemini" && "🪄 "}
                        {String(m.provedor).toUpperCase()}
                      </span>
                    )}
                    {typeof m.custo_estimado_reais === "number" && m.custo_estimado_reais > 0 && (
                      <span
                        className="inline-flex items-center px-1.5 py-0.5 rounded-sm border border-danger/40 bg-danger/10 text-danger font-semibold"
                        title="Custo estimado nominal em R$ para esta resposta (não inclui impostos nem overage)"
                      >
                        💸 ~R${Number(m.custo_estimado_reais).toFixed(2)}
                      </span>
                    )}
                    {m.roteamento_motivo && (
                      <span
                        className="text-muted max-w-full truncate"
                        title={m.roteamento_motivo}
                      >
                        ℹ️ {m.roteamento_motivo.length > 160 ? m.roteamento_motivo.slice(0, 158) + "…" : m.roteamento_motivo}
                      </span>
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
          {/* NOVO: Aviso dinâmico de PRIVACIDADE conforme provider selecionado */}
          {providerSelecionado === "local" ? (
            <div className="text-accent">🧠 Respostas 100% locais · NADA sai do seu PC · R$0,00</div>
          ) : providerSelecionado === "auto" ? (
            <div className="text-muted">🔮 Modo Automático: Prometeu prefere LOCAL. Usa API externa SÓ se valer a pena (tarefa complexa + teto ok).</div>
          ) : (
            <div className="text-danger font-semibold">
              ⚠️  Modo {String(providerSelecionado).toUpperCase()}:
              {" "}Conteúdo das mensagens ENVIADO para API externa de terceiro. Vai custar dinheiro (se tiver teto configurado).
            </div>
          )}
        </div>
      </div>
      </div>{/* fim área principal */}
    </div>
  );
}
