import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        ink: {
          50: "#f7f7f8",
          100: "#eceef1",
          200: "#d4d8df",
          400: "#8a93a0",
          600: "#4b5364",
          800: "#1f2533",
          900: "#0f1320",
        },
      },
    },
  },
  plugins: [],
};
export default config;
