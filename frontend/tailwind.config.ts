import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ============================================================
        //  DESIGN SYSTEM NEUROCORE — PERMANENTE (NÃO MUDAR)
        //  PRETO  #07070A  (bg-0 · fundo absoluto)
        //  ÂMBAR  #F59E0B  (accent principal)
        // ============================================================
        bg0: "#07070A",
        bg1: "#0D0D12",
        bg2: "#15151E",
        bg3: "#1E1E29",
        border1: "#262637",
        accent: "#F59E0B",
        "accent-soft": "#F59E0B26",
        "accent-bright": "#FBBF24",
        success: "#10B981",
        danger: "#EF4444",
        info: "#3B82F6",
        muted: "#9CA3AF",
        background: "#07070A",
        foreground: "#E5E7EB",
      },
      boxShadow: {
        glow: "0 0 0 1px #F59E0B33, 0 8px 30px -10px #F59E0B66",
      },
      fontFamily: {
        mono: ["var(--font-geist-mono)", "Consolas", "monospace"],
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;

