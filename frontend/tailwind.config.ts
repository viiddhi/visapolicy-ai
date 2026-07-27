import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#1E3A5F", light: "#2563EB", soft: "#EFF6FF" },
      },
    },
  },
  plugins: [],
};

export default config;
