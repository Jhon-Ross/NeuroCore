"use client";

// ================================================================
// HOOK: persistência LauncherConfig
// MVP usa localStorage (WebView do Tauri compartilha storage do app).
// Depois Task 8+ pode migrar para plugin-fs JSON em local_memory/launcher_config.json
// ================================================================

import { useEffect, useState } from "react";
import type { LauncherConfig } from "./types";

const STORAGE_KEY = "neurocore.launcher.config.v1";

const DEFAULTS: LauncherConfig = {
  abrir_chat_em_webview: true,
  manter_ollama_vivo_ao_sair: true,
  poll_interval_ms: 4000,
  tema: "preto_ambar",
};

export function useLauncherConfig() {
  const [cfg, setCfg] = useState<LauncherConfig>(DEFAULTS);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    try {
      if (typeof window === "undefined") return;
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        try {
          const parsed: any = JSON.parse(raw);
          setCfg({ ...DEFAULTS, ...parsed });
        } catch {}
      }
    } finally {
      setPronto(true);
    }
  }, []);

  function atualizar(patch: Partial<LauncherConfig>) {
    setCfg((ant) => {
      const prox = { ...ant, ...patch };
      try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prox)); } catch {}
      return prox;
    });
  }

  return { cfg, pronto, atualizar, defaults: DEFAULTS };
}
