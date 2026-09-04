import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        exon: {
          dark: "#05070d",
          card: "#0f172a",
          panel: "#1e293b",
          orange: "#FF5500",
          lime: "#CCFF00",
          cyan: "#00F0FF",
          border: "#000000",
        },
      },
      boxShadow: {
        brutal: "4px 4px 0px 0px #000000",
        "brutal-orange": "4px 4px 0px 0px #FF5500",
        "brutal-lime": "4px 4px 0px 0px #CCFF00",
        "brutal-cyan": "4px 4px 0px 0px #00F0FF",
        "brutal-sm": "2px 2px 0px 0px #000000",
        "brutal-lg": "6px 6px 0px 0px #000000",
      },
      fontFamily: {
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
