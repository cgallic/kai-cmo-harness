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
        background: "#101218",
        "bg-elevated": "#171a22",
        card: "#1c1f28",
        "card-hover": "#242833",
        border: "#303440",
        "border-hover": "#4a5160",
        foreground: "#fffaf0",
        "text-secondary": "#c2c0b8",
        "text-tertiary": "#82857f",
        cream: "#fffaf0",
        amber: {
          DEFAULT: "#5c8cff",
          light: "#8fb0ff",
          dim: "rgba(92,140,255,0.14)",
        },
        coral: {
          DEFAULT: "#f17c51",
          dim: "rgba(241,124,81,0.14)",
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
          DEFAULT: "#68c1d9",
          dim: "rgba(104,193,217,0.12)",
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
        DEFAULT: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
