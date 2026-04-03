import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        "bg-elevated": "#111111",
        card: "#141414",
        "card-hover": "#181818",
        border: "#1e1e1e",
        "border-hover": "#2a2a2a",
        foreground: "#fafafa",
        "text-secondary": "#a1a1a1",
        "text-tertiary": "#6b6b6b",
        cream: "#f2efe8",
        amber: {
          DEFAULT: "#f59e0b",
          light: "#fbbf24",
          dim: "rgba(245,158,11,0.12)",
        },
        success: {
          DEFAULT: "#22c55e",
          dim: "rgba(34,197,94,0.12)",
        },
        error: {
          DEFAULT: "#ef4444",
          dim: "rgba(239,68,68,0.12)",
        },
        info: {
          DEFAULT: "#3b82f6",
          dim: "rgba(59,130,246,0.12)",
        },
        purple: {
          DEFAULT: "#a78bfa",
          dim: "rgba(167,139,250,0.12)",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        body: ["var(--font-outfit)", "-apple-system", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      borderRadius: {
        DEFAULT: "12px",
        lg: "16px",
      },
    },
  },
  plugins: [],
};

export default config;
