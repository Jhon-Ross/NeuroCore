"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { usePainelStatus } from "./use_painel_status";
import {
  Sparkline,
  BarraProgresso,
  formatarUptime,
  seedFake,
} from "./ui_utils";

// ================================================================
// PAINEL DIREITO 320px REUTILIZAVEL (TODAS PAGINAS DO LAUNCHER)
// Sinais vitais, RPG Global, 7 Habilidades, Wall of Wins, Sparklines
// ================================================================

type Props = { pollMs?: number };

export function PainelDireito({ pollMs = 2500 }: Props) {
  const ps = usePainelStatus(pollMs);
  const histRef = useRef({
    cpu: [...seedFake(60, 7)],
    ram: [...seedFake(60, 11)],
    vram: [...seedFake(60, 13)],
    lat: [...seedFake(60, 17)].map((x) => x * 1.8),
  });
  const [, tick] = useState(0);
  useEffect(() => {
    const t = window.setInterval(() => {
      const H = histRef.current;
      const cpuNovo = Math.max(5, Math.min(95, H.cpu[H.cpu.length - 1] + (Math.random() * 12 - 6)));
      const ramNovo = Math.max(10, Math.min(90, H.ram[H.ram.length - 1] + (Math.random() * 4 - 2)));
      const vramNovo = ps.painel
        ? Math.max(10, Math.min(95, (ps.painel.vram.total_gb / 8) * 100 + (Math.random() * 6 - 3)))
        : Math.max(15, Math.min(90, H.vram[H.vram.length - 1] + (Math.random() * 3 - 1.5)));
      const latNovo =
        typeof ps.latenciaUltimaMs === "number"
          ? Math.max(5, Math.min(1500, ps.latenciaUltimaMs))
          : H.lat[H.lat.length - 1] + (Math.random() * 40 - 20);
      H.cpu.push(cpuNovo); H.ram.push(ramNovo); H.vram.push(vramNovo); H.lat.push(latNovo);
      if (H.cpu.length > 60) { H.cpu.shift(); H.ram.shift(); H.vram.shift(); H.lat.shift(); }
      tick((x) => (x + 1) % 1_000_000);
    }, 2000);
    return () => window.clearInterval(t);
  }, [ps.latenciaUltimaMs, ps.painel]);

  const { habilidades, feitos, xpTotal, nivelGlobal, xpParaProx, erro, painel, apiOnline } = ps;
  const xpFaltante = Math.max(0, xpParaProx - xpTotal);
  const H = histRef.current;
  const ultimo = (arr: number[]) => arr[arr.length - 1] ?? 0;

  return (
    <aside className="h-full w-full bg-bg1 border-l border-border1 flex flex-col overflow-hidden">
      {/* 1) Nivel Global */}
      <div className="h-36 px-5 py-4 border-b border-border1 bg-gradient-to-b from-bg2 to-bg1">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Nível Global</span>
          <span className="h-6 px-2 rounded-md bg-accent-soft border border-accent/40 text-accent text-[11px] font-bold grid place-items-center">
            LVL {nivelGlobal}
          </span>
        </div>
        <div className="flex items-end justify-between mb-2">
          <div className="leading-none">
            <div className="text-[26px] font-bold tracking-tight">
              {xpTotal}
              <span className="text-muted text-[13px] font-normal ml-1"> XP</span>
            </div>
            <div className="text-[11px] text-muted mt-1">
              Falta <span className="text-accent font-semibold">{xpFaltante} XP</span> para LVL {nivelGlobal + 1}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[11px] text-muted mb-0.5">Feitos</div>
            <div className="text-[20px] font-bold text-accent leading-none">{feitos.length}</div>
          </div>
        </div>
        <BarraProgresso xp={xpTotal} xpProx={xpParaProx} />
      </div>

      {/* 2) 7 Habilidades */}
      <div className="px-5 pt-3 pb-1 flex items-center justify-between shrink-0">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">7 Habilidades · Regiões</span>
        <span className="text-[10px] text-muted">Fase N/5</span>
      </div>
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1.5 min-h-0">
        {habilidades.map((h) => (
          <div
            key={h.id}
            className={
              "rounded-lg px-3 py-2 border transition " +
              (h.ativo
                ? "bg-bg2 border-accent/30 shadow-[0_0_0_1px_#F59E0B22]"
                : "bg-bg1/50 border-border1 opacity-80")
            }
          >
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[14px]">{h.icone}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="truncate text-[12.5px] font-semibold">
                    {h.nome}
                    {h.ativo && (
                      <span className="ml-1.5 text-[9px] font-bold uppercase tracking-wider text-success">
                        ● ativa
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-muted font-mono shrink-0">
                    LVL {h.nivel} · f{h.fase}
                  </div>
                </div>
                <div className="text-[10px] text-muted truncate font-mono">{h.regiao}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <BarraProgresso xp={h.xp} xpProx={h.xp_para_prox} />
              </div>
              <div className="text-[10px] text-muted font-mono w-[54px] text-right">
                {h.xp}/{h.xp_para_prox}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 3) Wall of Wins */}
      <div className="px-5 py-2 flex items-center justify-between border-t border-border1 shrink-0">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Wall of Wins · Feitos</span>
        <span className="text-[10px] text-accent font-bold">{feitos.length} conquistas</span>
      </div>
      <div className="px-3 pb-3 space-y-1.5 max-h-32 overflow-y-auto shrink-0">
        {feitos.slice(0, 4).map((f) => (
          <div key={f.id} className="rounded-lg px-3 py-2 bg-bg2 border border-border1">
            <div className="flex items-start gap-2">
              <div className="text-[15px] mt-0.5">{f.emoji}</div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-semibold leading-tight">{f.nome}</div>
                <div className="text-[10.5px] text-muted leading-relaxed mt-0.5">{f.descricao}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 4) Sparklines Hardware + Latencia */}
      <div className="px-5 py-2 flex items-center justify-between border-t border-border1 shrink-0">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted">Hardware · 60s</span>
        <span className="text-[10px] text-muted">Uptime {formatarUptime(painel?.uptime_segundos)}</span>
      </div>
      <div className="px-3 pb-3 grid grid-cols-2 gap-2 shrink-0">
        {[
          { nome: "CPU",  cor: "#F59E0B", pct: Math.round(ultimo(H.cpu)) },
          { nome: "RAM",  cor: "#3B82F6", pct: Math.round(ultimo(H.ram)) },
          { nome: "VRAM", cor: "#10B981", pct: Math.round(ultimo(H.vram)) },
          { nome: "Lat",  cor: "#EF4444", pct: Math.round(ultimo(H.lat)) },
        ].map((s) => (
          <div key={s.nome} className="rounded-lg bg-bg2 border border-border1 p-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted">{s.nome}</span>
              <span className="text-[10px] font-mono font-semibold" style={{ color: s.cor }}>
                {s.nome === "Lat" ? `${s.pct}ms` : `${s.pct}%`}
              </span>
            </div>
            <Sparkline
              data={s.nome === "CPU" ? H.cpu : s.nome === "RAM" ? H.ram : s.nome === "VRAM" ? H.vram : H.lat}
              cor={s.cor}
            />
          </div>
        ))}
      </div>

      {/* 5) Status API (rodape) */}
      <div className="px-4 py-2 border-t border-border1 text-[10.5px] shrink-0 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-muted">
          <span
            className={
              "inline-block h-1.5 w-1.5 rounded-full align-middle " +
              (apiOnline === false ? "bg-danger" : "bg-success shadow-[0_0_6px_#10B981]")
            }
          />
          API :8000 · <span className={apiOnline === false ? "text-danger font-semibold ml-1" : "text-success font-semibold ml-1"}>
            {apiOnline === false ? "OFFLINE" : apiOnline === null ? "…" : "CONECTADO"}
          </span>
        </span>
        <span className="text-muted">R$ 0,00</span>
      </div>
    </aside>
  );
}
