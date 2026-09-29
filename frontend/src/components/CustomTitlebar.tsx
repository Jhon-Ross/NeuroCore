"use client";

import React, { useMemo, useState } from "react";
import { useTauriEnv } from "./use_tauri_env";

// ================================================================
// TITLEBAR CUSTOM DO LAUNCHER (decorations: false no tauri)
// Barra 32px no topo, fundo ÂMBAR/PRETO com gradiente, drag area,
// botões min / maximize / close e status da aplicação.
// ================================================================

export function CustomTitlebar() {
  const tauri = useTauriEnv();
  const [estado, setEstado] = useState<"idle" | "min" | "max" | "close">("idle");

  const wm = useMemo(() => {
    let cache: any = null;
    return async () => {
      if (cache) return cache;
      try {
        // Usa plugin-window se instalado, ou cai para @tauri-apps/api/window padrão
        let mod: any = null;
        try {
          // @ts-ignore dynamic
          mod = await import(/* webpackIgnore: true */ "@tauri-apps/plugin-window");
        } catch {
          // @ts-ignore dynamic
          mod = await import("@tauri-apps/api/window").catch(() => null);
        }
        if (mod && typeof mod.getCurrentWindow === "function") {
          cache = mod.getCurrentWindow();
        }
      } catch { cache = null; }
      return cache;
    };
  }, []);

  async function dragStart(e: React.MouseEvent) {
    if (!tauri.isTauri) return;
    if (e.button !== 0) return;
    try {
      const win: any = await wm();
      if (win && typeof win.startDragging === "function") {
        await win.startDragging();
      } else {
        await tauri.invoke("plugin:window|start_dragging").catch(() => {});
      }
    } catch {}
  }

  async function acao(kind: "min" | "max" | "close") {
    if (!tauri.isTauri) return;
    setEstado(kind);
    try {
      const win: any = await wm();
      if (!win) {
        // fallback invokes Rust-side
        await tauri.invoke(
          kind === "min"
            ? "plugin:window|minimize"
            : kind === "max"
              ? "plugin:window|toggle_maximize"
              : "plugin:window|close",
        ).catch(() => {});
        return;
      }
      if (kind === "min" && typeof win.minimize === "function") await win.minimize();
      if (kind === "max" && typeof win.toggleMaximize === "function") await win.toggleMaximize();
      if (kind === "close" && typeof win.close === "function") await win.close();
    } finally {
      setTimeout(() => setEstado("idle"), 350);
    }
  }

  return (
    <div
      className="h-8 w-full shrink-0 select-none text-[11.5px] flex items-stretch justify-between backdrop-blur-md
                 bg-gradient-to-r from-[#0c0a08] via-[#140f07] to-[#1c1404]
                 border-b border-[#F59E0B]/40 text-muted"
    >
      {/* Drag area esquerda */}
      <div className="flex-1 flex items-center px-3 gap-3 cursor-grab active:cursor-grabbing"
           onMouseDown={dragStart}>
        <div className="h-5 w-5 rounded-md bg-accent/90 grid place-items-center text-bg0 font-bold text-[11px] shadow-[0_0_6px_#F59E0B88]">
          P
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-accent tracking-wide">NeuroCore Launcher</span>
          <span className="text-muted/70">·</span>
          <span className="text-muted/90" suppressHydrationWarning>
            {!tauri.ready
              ? "Carregando…"
              : tauri.isTauri
                ? "Desktop WebView2 · Tauri v2"
                : "Navegador Web · Modo Preview"}
          </span>
          {estado !== "idle" && (
            <span className="ml-2 inline-block px-2 py-0.5 rounded bg-bg2 border border-border1 text-[10.5px]">
              {estado === "min" ? "⏵ minimizando" : estado === "max" ? "⤡ maximizando" : "✕ fechando"}
            </span>
          )}
        </div>
      </div>

      {/* Botões janela */}
      <div className="flex items-stretch divide-x divide-border1/40">
        <button
          aria-label="Minimizar"
          onClick={() => acao("min")}
          disabled={!tauri.isTauri}
          className="w-11 grid place-items-center hover:bg-bg3/70 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="Minimizar (Win+↓)"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden><rect x="1" y="4.5" width="8" height="1" fill="currentColor"/></svg>
        </button>
        <button
          aria-label="Maximizar"
          onClick={() => acao("max")}
          disabled={!tauri.isTauri}
          className="w-11 grid place-items-center hover:bg-bg3/70 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="Maximizar / Restaurar (Win+↑)"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden><rect x="1" y="1" width="8" height="8" fill="none" stroke="currentColor" strokeWidth="1"/></svg>
        </button>
        <button
          aria-label="Fechar"
          onClick={() => acao("close")}
          disabled={!tauri.isTauri}
          className="w-11 grid place-items-center hover:bg-danger hover:text-bg0 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="Fechar (X · CloseRequested stop_all ≤8s)"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
            <path d="M1 1 L9 9 M9 1 L1 9" stroke="currentColor" strokeWidth="1.2"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
