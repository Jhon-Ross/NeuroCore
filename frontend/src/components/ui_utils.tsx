"use client";

import React from "react";

// ================================================================
// UI UTILS — Componentes Pequenos Reutilizáveis no Launcher
// Sparkline, BarraProgresso, Cards, etc
// Mantem paleta PRETO #07070A + AMBAR #F59E0B
// ================================================================

export function Sparkline({
  data,
  cor,
  height = 30,
}: {
  data: number[];
  cor: string;
  height?: number;
}) {
  const w = 180;
  const h = height;
  const arr = data.length >= 2 ? data : [0, 0];
  const min = Math.min(...arr);
  const max = Math.max(...arr);
  const range = Math.max(1e-6, max - min);
  const pontos = arr
    .map((v, i) => {
      const x = (i / (arr.length - 1)) * w;
      const y = h - ((v - min) / range) * h * 0.92 - h * 0.04;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible pointer-events-none">
      <polyline fill="none" stroke={cor} strokeWidth="1.5" points={pontos} />
    </svg>
  );
}

export function BarraProgresso({
  xp,
  xpProx,
  cor = "#F59E0B",
}: {
  xp: number;
  xpProx: number;
  cor?: string;
}) {
  const pct = Math.min(100, Math.max(0, Math.round((xp / Math.max(1, xpProx)) * 100)));
  return (
    <div className="h-1.5 w-full rounded-full bg-bg3 overflow-hidden">
      <div
        className="h-full rounded-full transition-[width] duration-700"
        style={{
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${cor} 0%, ${cor}cc 100%)`,
        }}
      />
    </div>
  );
}

export function formatarDataIso(iso?: string | null, fallback?: string): string {
  if (!iso) return fallback ?? "hoje";
  try {
    const d = new Date(iso);
    const dd = d.getDate().toString().padStart(2, "0");
    const mm = (d.getMonth() + 1).toString().padStart(2, "0");
    const hh = d.getHours().toString().padStart(2, "0");
    const ii = d.getMinutes().toString().padStart(2, "0");
    return `${dd}/${mm} ${hh}:${ii}`;
  } catch {
    return fallback ?? iso;
  }
}

export function formatarUptime(seg?: number): string {
  if (!seg || isNaN(seg)) return "—";
  const s = Math.max(0, Math.floor(seg));
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

export function seedFake(len = 60, seed = 42): number[] {
  let s = seed;
  const out: number[] = [];
  for (let i = 0; i < len; i++) {
    s = (s * 9301 + 49297) % 233280;
    const rnd = s / 233280;
    out.push(25 + rnd * 65);
  }
  return out;
}

export function CirculoStatus({
  online,
  suppressHydrationWarning,
}: {
  online: boolean;
  suppressHydrationWarning?: boolean;
}) {
  return (
    <span
      suppressHydrationWarning={suppressHydrationWarning}
      className={`inline-block h-2 w-2 rounded-full align-middle ${
        online ? "bg-success shadow-[0_0_6px_#10B981]" : "bg-danger/70"
      }`}
    />
  );
}

export function Card({
  title,
  icon,
  right,
  children,
  className = "",
}: {
  title?: React.ReactNode;
  icon?: string;
  right?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={
        "rounded-xl border border-border1 bg-bg1 " +
        "px-4 py-3 shadow-[0_1px_0_0_#ffffff08_inset] transition " +
        className
      }
    >
      {(title || right) && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
            {icon && <span className="text-[13px]">{icon}</span>}
            {title}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}
