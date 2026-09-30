"use client";

// ================================================================
// COMPONENTE: ChatHistorySidebar
// Painel lateral esquerdo do Chat — lista as sessões SQLite,
// permite iniciar nova conversa e alternar entre históricos.
// Paleta oficial: PRETO #07070A + ÂMBAR #F59E0B.
// ================================================================

import React, { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "./use_painel_status";

interface SessaoItem {
  id: number;
  titulo: string;
  criado_em: string;
  atualizado_em: string;
  total_mensagens: number;
}

interface ChatHistorySidebarProps {
  sessionIdAtiva: number | null;
  onSelecionarSessao: (id: number) => void;
  onNovaSessao: () => void;
  recarregarTrigger?: number;
  /** Estado da API vindo do hook usePainelStatus:
   *   true  = API tá online e respondendo 200.
   *   false = API definitivamente offline (já falhou 2+ vezes ou timeout).
   *   null  = API ainda está "sondando / inicializando" (primeiros segundos do app). */
  apiOnline?: boolean | null;
}

function formatarData(iso: string): string {
  if (!iso) return "";
  try {
    const d = new Date(iso.replace(" ", "T") + (iso.includes("Z") ? "" : "Z"));
    const agora = new Date();
    const diffMs = agora.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "agora";
    if (diffMin < 60) return `${diffMin}m atrás`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}h atrás`;
    const diffD = Math.floor(diffH / 24);
    if (diffD < 7) return `${diffD}d atrás`;
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
  } catch {
    return "";
  }
}

export function ChatHistorySidebar({
  sessionIdAtiva,
  onSelecionarSessao,
  onNovaSessao,
  recarregarTrigger = 0,
  apiOnline = null,
}: ChatHistorySidebarProps) {
  const [sessoes, setSessoes] = useState<SessaoItem[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const isMountedRef = useRef(true);
  const apiOnlinePrevRef = useRef<boolean | null>(apiOnline);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const r = await fetch(`${API_BASE}/api/chat/sessions?limite=60`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const dados = await r.json();
      if (isMountedRef.current) setSessoes(dados.sessoes ?? []);
    } catch (e: unknown) {
      if (!isMountedRef.current) return;
      const msgBruta = e instanceof Error ? e.message : String(e ?? "Erro ao buscar sessões");
      // Trata erros de "API ainda não ligou" / connection refused / DNS / Mixed Content etc
      // de forma AMIGÁVEL (sem vermelho no 1º load e sem gritar 'Failed to fetch')
      const ehFalhaConexaoInicial =
        /Failed to fetch|NetworkError|request to .* failed|TypeError: fetch|ERR_CONNECTION_REFUSED|ECONNREFUSED|aborted|timeout|timed out/i.test(msgBruta) ||
        msgBruta.toLowerCase().includes("load failed") ||
        msgBruta.toLowerCase().includes("typeerror");
      if (ehFalhaConexaoInicial) {
        // NÃO marca erro VERMELHO se for apenas "API ainda inicializando".
        // Mostra um texto amarelo/neutro NA ÁREA DA LISTA se não tiver sessoes.
        setErro(null);
      } else {
        // Erro REAL (ex: HTTP 500 / 404)
        setErro(msgBruta);
      }
    } finally {
      if (isMountedRef.current) setCarregando(false);
    }
  }, []);

  // (1) Carrega uma vez no mount + toda vez que recarregarTrigger mudar (usuario clicka atualizar)
  useEffect(() => {
    isMountedRef.current = true;
    carregar();
    return () => { isMountedRef.current = false; };
  }, [carregar, recarregarTrigger]);

  // (2) TRIGGER IMPORTANTE: SEMPRE recarrega o histórico AUTOMATICAMENTE
  //     quando a API transicionar de (null | false) → true.
  //     Isto resolve o bug do print do Jhon: "Só depois de fechar e abrir de novo que carrega".
  //     Antes, a sidebar era montada só uma vez e nunca mais tentava, mesmo quando a API subia.
  useEffect(() => {
    const prev = apiOnlinePrevRef.current;
    if (prev !== true && apiOnline === true) {
      // acabou de ficar ONLINE → força fetch agora
      carregar();
    }
    apiOnlinePrevRef.current = apiOnline;
  }, [apiOnline, carregar]);

  // (3) RETRY INTELIGENTE ENQUANTO API ESTÁ INDEFINIDA (null = sondando inicial):
  //     a cada 4s, tenta de novo carregar o histórico se ainda não temos sessoes
  //     e ainda houve uma falha de conexão. Isso evita que o usuário precise
  //     do "fechar e abrir aba" para sincronizar.
  useEffect(() => {
    if (apiOnline === true || sessoes.length > 0 || !!erro) {
      // API já online / já temos dados / erro real → não fazer retry automático
      return;
    }
    const timer = window.setInterval(() => {
      if (!isMountedRef.current) return;
      carregar();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [apiOnline, sessoes.length, erro, carregar]);

  return (
    <div className="flex flex-col h-full w-full bg-[#06060C] border-r border-border1 select-none">
      {/* Cabeçalho */}
      <div className="px-3 pt-4 pb-2 shrink-0">
        <div className="text-[10px] font-bold uppercase tracking-widest text-muted/60 mb-2 px-1">
          Conversas
        </div>
        <button
          onClick={onNovaSessao}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-accent/10 border border-accent/30 text-accent text-[12px] font-semibold hover:bg-accent/20 hover:border-accent/60 hover:shadow-[0_0_14px_rgba(245,158,11,0.15)] active:scale-[0.98] transition-all duration-150"
        >
          <span className="text-[14px] leading-none">✦</span>
          <span>Nova Conversa</span>
        </button>
      </div>

      {/* Lista de Sessões */}
      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-0.5">
        {carregando && sessoes.length === 0 && (
          <div className="flex items-center gap-2 px-3 py-4 text-[11px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent/60 animate-pulse" />
            <span>Carregando histórico...</span>
          </div>
        )}
        {erro && (
          <div className="mx-1 mt-2 px-3 py-2 rounded-lg bg-danger/10 border border-danger/20 text-danger text-[10.5px]">
            ⚠️ {erro}
          </div>
        )}
        {!carregando && !erro && sessoes.length === 0 && apiOnline === true && (
          <div className="px-3 py-5 text-center text-muted text-[11px]">
            <div className="text-2xl mb-2 opacity-30">💬</div>
            <div>Nenhuma conversa ainda.</div>
            <div className="mt-1 opacity-70">Inicie um chat acima.</div>
          </div>
        )}
        {!carregando && !erro && sessoes.length === 0 && apiOnline === false && (
          <div className="px-3 py-5 text-center text-muted text-[11px]">
            <div className="text-2xl mb-2 opacity-30">🔌</div>
            <div>API FastAPI offline.</div>
            <div className="mt-1 opacity-70">Clique em <b>Ligar Tudo</b> no Launcher.</div>
            <button
              onClick={carregar}
              disabled={carregando}
              className="mt-3 px-3 py-1 rounded-md border border-accent/40 text-accent text-[10.5px] hover:bg-accent/10 disabled:opacity-50"
            >
              ⟳ Tentar novamente
            </button>
          </div>
        )}
        {!carregando && !erro && sessoes.length === 0 && (apiOnline === null || apiOnline === undefined) && (
          <div className="px-3 py-5 text-center text-[11px]">
            <div className="text-2xl mb-2 opacity-60">⏳</div>
            <div className="text-accent/80 font-medium">Aguardando API :8000 inicializar...</div>
            <div className="mt-1 text-muted/70 opacity-80">Isso é normal enquanto o Launcher termina de ligar tudo.</div>
            <div className="mt-1 text-muted/60 opacity-70">Atualiza automaticamente a cada 4 segundos.</div>
            <button
              onClick={carregar}
              disabled={carregando}
              className="mt-3 px-3 py-1 rounded-md border border-border1 text-muted text-[10.5px] hover:bg-bg2 disabled:opacity-50"
            >
              ⟳ Tentar agora
            </button>
          </div>
        )}
        {sessoes.map((s) => {
          const ativo = s.id === sessionIdAtiva;
          return (
            <button
              key={s.id}
              onClick={() => onSelecionarSessao(s.id)}
              title={s.titulo}
              className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-100 group ${ativo ? "bg-accent/15 border border-accent/40 text-foreground" : "hover:bg-bg2 border border-transparent text-foreground/70 hover:text-foreground"}`}
            >
              <div className="flex items-start gap-2">
                <span className="mt-0.5 text-[11px] shrink-0 opacity-60">
                  {ativo ? "▶" : "💬"}
                </span>
                <div className="flex-1 min-w-0">
                  <div className={`text-[11.5px] font-medium leading-tight truncate ${ativo ? "text-accent" : ""}`}>
                    {s.titulo || "Conversa sem título"}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[9.5px] text-muted/60">{formatarData(s.atualizado_em)}</span>
                    {s.total_mensagens > 0 && (
                      <>
                        <span className="text-muted/30 text-[9px]">·</span>
                        <span className="text-[9.5px] text-muted/50">{s.total_mensagens} msg{s.total_mensagens !== 1 ? "s" : ""}</span>
                      </>
                    )}
                  </div>
                </div>
                {ativo && <span className="mt-1 h-1.5 w-1.5 rounded-full bg-accent shrink-0 animate-pulse" />}
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div className="shrink-0 px-3 pb-3 pt-1 border-t border-border1/40">
        <button
          onClick={carregar}
          disabled={carregando}
          className="w-full text-[9.5px] text-muted/50 hover:text-muted transition py-1 flex items-center justify-center gap-1.5"
        >
          <span className={carregando ? "animate-spin inline-block" : ""}>⟳</span>
          {carregando ? "Atualizando..." : "Atualizar lista"}
        </button>
      </div>
    </div>
  );
}
