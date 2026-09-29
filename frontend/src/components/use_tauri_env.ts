"use client";

// ================================================================
// HOOK: detecta se estamos dentro do WebView do Tauri ou em navegador
// Também centraliza import do @tauri-apps/api com fallback silencioso
//
// 🔒 REGRA SSR-SAFE (evita Hydration Mismatch Next.js):
//   - No SSR (window === undefined), isTauri SEMPRE = false.
//   - No 1º render do cliente (antes do useEffect), isTauri CONTINUA = false (para coincidir com o servidor).
//   - Após o useEffect disparar no cliente (ready = true), aí sim setamos isTauri=true
//     se detectarmos __TAURI_INTERNALS__ ou os plugins carregarem.
//   - Isso custa 1 frame (0ms ~ 16ms) de "falso navegador", mas ELIMINA mismatch.
// ================================================================

import { useEffect, useState } from "react";

export type TauriEnv = {
  ready: boolean;
  isTauri: boolean;
  invoke: <T = any>(cmd: string, args?: Record<string, any>) => Promise<T>;
  listen: (
    event: string,
    cb: (payload: any) => void,
  ) => Promise<() => void> | (() => void);
  shellOpen: (url: string) => Promise<void>;
};

function noopInvoke<T>(cmd: string, _args?: Record<string, any>): Promise<T> {
  return Promise.reject(
    new Error(`[Launcher] Comando Tauri "${cmd}" indisponível (ambiente navegador).`),
  );
}
function noopListen(_e: string, _cb: any) {
  return () => {};
}
async function noopShellOpen(url: string) {
  if (typeof window !== "undefined") window.open(url, "_blank", "noopener");
}

function detectarSincrono(): boolean {
  // Apenas usado DENTRO do useEffect (cliente-side) para confirmar ambiente.
  if (typeof window === "undefined") return false;
  const w = window as any;
  return !!(
    w.__TAURI__ ||
    w.__TAURI_INTERNALS__ ||
    w.__TAURI_IPC__ ||
    w.__TAURI_CORE__ ||
    (w.location && w.location.protocol === "tauri:")
  );
}

export function useTauriEnv(): TauriEnv {
  // SSR SAFE inicial: TUDO igual no servidor e no 1º paint cliente.
  const [isTauri, setIsTauri] = useState<boolean>(false);
  const [ready, setReady] = useState<boolean>(false);
  const [api, setApi] = useState<{
    invoke: typeof noopInvoke;
    listen: typeof noopListen;
    shellOpen: typeof noopShellOpen;
  }>({
    invoke: noopInvoke,
    listen: noopListen,
    shellOpen: noopShellOpen,
  });

  useEffect(() => {
    let mounted = true;
    (async () => {
      // PRIMEIRO: detecção SÍNCRONA DOS GLOBALS TAURI (100% confiável no desktop WebView2,
      // independe do pacote npm @tauri-apps/api carregar via dynamic import).
      // Se o usuário estiver no launcher desktop, essa variável é true agora.
      const sync = detectarSincrono();

      // Invoke FALLBACK: se globals existem, usamos window.__TAURI__.invoke / .listen
      // DIRETO SEM PRECISAR do dynamic import do módulo npm. Isso evita 100% de
      // "isTauri=true mas invoke=noop" (causa do banner vermelho do print do usuário).
      function invokeFallbackNative<T>(cmd: string, args?: Record<string, any>): Promise<T> {
        try {
          const w = window as any;
          // Tauri v2 expõe ambos locais comuns.
          const core = w.__TAURI__?.core ?? w.__TAURI_CORE__ ?? w.__TAURI_INTERNALS__?.core ?? w.__TAURI_INTERNALS__;
          if (core && typeof core.invoke === "function") {
            return Promise.resolve(core.invoke(cmd, args));
          }
          if (typeof w.__TAURI_IPC__ === "object" && w.__TAURI_IPC__ && typeof w.__TAURI_IPC__.invoke === "function") {
            return Promise.resolve(w.__TAURI_IPC__.invoke(cmd, args));
          }
          // Tauri v1 compat:
          if (typeof w.__TAURI__?.invoke === "function") {
            return Promise.resolve(w.__TAURI__.invoke(cmd, args));
          }
        } catch (e) {
          return Promise.reject(e);
        }
        return noopInvoke<T>(cmd, args);
      }
      function listenFallbackNative(event: string, cb: (payload: any) => void) {
        try {
          const w = window as any;
          const core = w.__TAURI__?.event ?? w.__TAURI_CORE__?.event ?? w.__TAURI_INTERNALS__?.event ?? w.__TAURI_INTERNALS__;
          if (core && typeof core.listen === "function") {
            const p = core.listen(event, cb) as PromiseLike<() => void>;
            // Tauri .listen retorna Promise<unsubscribe>. Wrap em unsubscribe síncrono
            // para bater com a tipagem do TauriEnv.
            let unsub: null | (() => void) = null;
            void Promise.resolve(p).then((fn) => {
              unsub = fn;
            });
            return () => {
              if (typeof unsub === "function") unsub();
            };
          }
          if (typeof w.__TAURI__?.listen === "function") {
            const p = w.__TAURI__.listen(event, cb) as PromiseLike<() => void>;
            let unsub: null | (() => void) = null;
            void Promise.resolve(p).then((fn) => {
              unsub = fn;
            });
            return () => {
              if (typeof unsub === "function") unsub();
            };
          }
        } catch {}
        return noopListen(event, cb);
      }

      try {
        const PLUGIN_CORE = "@tauri-apps/api/core";
        const mod: any = await (async () => {
          try {
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            return await import(/* webpackIgnore: true */ PLUGIN_CORE);
          } catch {
            return null;
          }
        })();
        let shellOpen: (u: string) => Promise<void> = noopShellOpen;
        try {
          const PLUGIN_OPENER = "@tauri-apps/plugin-opener";
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          const p2: any = await (async () => { try { return await import(/* webpackIgnore: true */ PLUGIN_OPENER); } catch { return null; } })();
          if (p2 && typeof p2.open === "function") shellOpen = (u: string) => p2.open(u);
        } catch {}

        // ✅ Critério isTauri final:
        // Primeiro detecção síncrona (SUPERIOR, pois depende de window globals nativas),
        // só cai no !!mod caso a detecção sync dê falso mas plugin npm carregou.
        const ok = sync || !!mod;

        if (!mounted) return;
        setIsTauri(ok);
        if (ok) {
          setApi({
            invoke:
              mod && typeof (mod as any).invoke === "function"
                ? (mod as any).invoke
                : invokeFallbackNative,
            listen:
              mod && typeof (mod as any).listen === "function"
                ? (mod as any).listen
                : listenFallbackNative,
            shellOpen,
          });
        } else {
          setApi({
            invoke: noopInvoke,
            listen: noopListen,
            shellOpen,
          });
        }
      } catch {
        if (mounted) {
          const ok_sync = detectarSincrono();
          setIsTauri(ok_sync);
          if (ok_sync) {
            setApi({
              invoke: invokeFallbackNative,
              listen: listenFallbackNative,
              shellOpen: noopShellOpen,
            });
          } else {
            setApi({
              invoke: noopInvoke,
              listen: noopListen,
              shellOpen: noopShellOpen,
            });
          }
        }
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return { ready, isTauri, ...api };
}
