"use client";

// ================================================================
// COMPONENTE: CodeBlockRunner
// Renderiza blocos de código markdown com syntax visual,
// botão de copiar e CODE RUNNER SEGURO via POST /api/code/run.
// Paleta oficial: PRETO #07070A + ÂMBAR #F59E0B.
// ================================================================

import React, { useState } from "react";
import { API_BASE } from "./use_painel_status";

interface CodeBlockRunnerProps {
  code: string;
  language?: string;
  onXpGanho?: (xp: number) => void;
}

interface ResultadoExecucao {
  sucesso: boolean;
  stdout: string;
  stderr: string;
  codigo_retorno: number;
  tempo_ms: number;
  linguagem: string;
  xp_ganho: number;
}

export function CodeBlockRunner({ code, language = "python", onXpGanho }: CodeBlockRunnerProps) {
  const [copiado, setCopiado] = useState(false);
  const [executando, setExecutando] = useState(false);
  const [saida, setSaida] = useState<ResultadoExecucao | null>(null);
  const [drawerAberto, setDrawerAberto] = useState(false);
  const [erroRede, setErroRede] = useState<string | null>(null);

  const langLimpo = (language || "python").toLowerCase().trim();
  const podeExecutar = ["python", "py", "powershell", "ps1", "javascript", "js", "node", "bash", "sh"].includes(langLimpo);

  async function handleCopiar() {
    try {
      await navigator.clipboard.writeText(code);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // Fallback manual se permissão falhar
      const el = document.createElement("textarea");
      el.value = code;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    }
  }

  async function handleExecutar() {
    if (executando) return;
    setExecutando(true);
    setDrawerAberto(true);
    setErroRede(null);

    try {
      const resp = await fetch(`${API_BASE}/api/code/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          codigo: code,
          linguagem: langLimpo,
          timeout_segundos: 15,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Servidor retornou status HTTP ${resp.status}`);
      }

      const dados: ResultadoExecucao = await resp.json();
      setSaida(dados);

      if (dados.xp_ganho > 0 && onXpGanho) {
        onXpGanho(dados.xp_ganho);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErroRede(`Não foi possível conectar à API :8000 (${msg}). Verifique se os serviços estão ligados.`);
    } finally {
      setExecutando(false);
    }
  }

  // Ícone por linguagem
  function getIconeLang(l: string) {
    if (l === "python" || l === "py") return "🐍";
    if (l === "powershell" || l === "ps1") return "💻";
    if (l === "javascript" || l === "js" || l === "node") return "⚡";
    if (l === "bash" || l === "sh") return "🐚";
    return "📜";
  }

  return (
    <div className="my-3 rounded-xl border border-border1 bg-[#09090E] overflow-hidden shadow-lg transition">
      {/* Top Bar do Bloco de Código */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#0F0F17] border-b border-border1 text-[11px]">
        <div className="flex items-center gap-1.5 font-mono font-medium text-muted uppercase tracking-wider">
          <span>{getIconeLang(langLimpo)}</span>
          <span className="text-[10px] text-foreground/80">{langLimpo || "código"}</span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Botão Copiar */}
          <button
            type="button"
            onClick={handleCopiar}
            className="px-2 py-0.5 rounded text-[10.5px] text-muted hover:text-foreground hover:bg-bg2 transition border border-transparent hover:border-border1"
            title="Copiar código"
          >
            {copiado ? "✅ Copiado!" : "📋 Copiar"}
          </button>

          {/* Botão Executar (Code Runner) */}
          {podeExecutar && (
            <button
              type="button"
              onClick={handleExecutar}
              disabled={executando}
              className={`px-2.5 py-0.5 rounded text-[11px] font-semibold flex items-center gap-1 transition ${
                executando
                  ? "bg-accent/20 text-accent/60 cursor-wait border border-accent/30"
                  : "bg-accent/15 text-accent border border-accent/40 hover:bg-accent/25 hover:border-accent hover:shadow-[0_0_12px_rgba(245,158,11,0.2)] active:scale-95"
              }`}
              title="Executar este código na sandbox local do NeuroCore"
            >
              {executando ? (
                <>
                  <span className="inline-block h-2 w-2 rounded-full bg-accent animate-ping" />
                  <span>Executando...</span>
                </>
              ) : (
                <>
                  <span>▶️</span>
                  <span>Executar</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Área de Visualização do Código */}
      <div className="relative">
        <pre className="p-3.5 text-[12.5px] font-mono leading-relaxed overflow-x-auto text-emerald-100/90 selection:bg-accent/30 selection:text-white">
          <code>{code}</code>
        </pre>
      </div>

      {/* Drawer / Mini Terminal de Saída */}
      {drawerAberto && (
        <div className="border-t border-border1 bg-[#050508] animate-in fade-in duration-150">
          {/* Header do Terminal */}
          <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#0B0B12] border-b border-border1/60 text-[10.5px]">
            <div className="flex items-center gap-2">
              {executando ? (
                <div className="flex items-center gap-1.5 text-accent">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                  <span className="font-semibold">Sandbox executando subprocesso...</span>
                </div>
              ) : erroRede ? (
                <div className="flex items-center gap-1.5 text-danger font-semibold">
                  <span>⚠️</span>
                  <span>Falha de Conexão</span>
                </div>
              ) : saida ? (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="flex items-center gap-1">
                    {saida.sucesso ? "🟢" : "🔴"}
                    <span className={saida.sucesso ? "text-success font-semibold" : "text-danger font-semibold"}>
                      {saida.sucesso ? "Sucesso" : "Falhou"}
                    </span>
                  </span>
                  <span className="text-muted">·</span>
                  <span className="text-muted font-mono">{saida.tempo_ms}ms</span>
                  <span className="text-muted">·</span>
                  <span className="text-muted font-mono">Exit: {saida.codigo_retorno}</span>
                  {saida.xp_ganho > 0 && (
                    <span className="font-bold text-accent px-1.5 py-0.2 rounded border border-accent/40 bg-accent/10">
                      ✨ +{saida.xp_ganho} XP Código
                    </span>
                  )}
                </div>
              ) : null}
            </div>

            <button
              type="button"
              onClick={() => setDrawerAberto(false)}
              className="text-muted hover:text-foreground text-[10.5px] px-1.5 py-0.5 rounded hover:bg-bg2 transition"
              title="Fechar saída"
            >
              ✕ Fechar
            </button>
          </div>

          {/* Conteúdo do Terminal */}
          <div className="p-3 font-mono text-[11.5px] max-h-56 overflow-y-auto leading-relaxed">
            {executando && (
              <div className="text-muted text-[11px] flex items-center gap-2 py-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent animate-ping" />
                <span>Aguardando retorno do processo no Windows... (timeout: 15s)</span>
              </div>
            )}

            {erroRede && (
              <div className="text-danger text-[11.5px] bg-danger/10 border border-danger/20 p-2 rounded">
                {erroRede}
              </div>
            )}

            {saida && !executando && (
              <div className="space-y-2">
                {saida.stdout && (
                  <div>
                    <div className="text-[9.5px] font-semibold text-muted uppercase tracking-wider mb-1">STDOUT</div>
                    <pre className="text-zinc-100 whitespace-pre-wrap break-words">{saida.stdout}</pre>
                  </div>
                )}

                {saida.stderr && (
                  <div>
                    <div className="text-[9.5px] font-semibold text-danger uppercase tracking-wider mb-1">STDERR / ERRO</div>
                    <pre className="text-red-300 whitespace-pre-wrap break-words">{saida.stderr}</pre>
                  </div>
                )}

                {!saida.stdout && !saida.stderr && (
                  <div className="text-muted italic text-[11px]">
                    (Processo finalizou com código {saida.codigo_retorno} sem imprimir mensagens)
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
