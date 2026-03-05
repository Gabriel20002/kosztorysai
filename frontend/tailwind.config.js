/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#1392ec",
        secondary: "#8b5cf6",
        "background-light": "#f6f7f8",
        "background-dark": "#0B1015",
        "surface-dark": "#151C24",
        "surface-light": "#ffffff",
        "accent-blue": "#1e40af",
        "accent-purple": "#4c1d95",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        sans: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      backgroundImage: {
        'glow-gradient': 'radial-gradient(circle at 50% 50%, rgba(19, 146, 236, 0.15) 0%, rgba(11, 16, 21, 0) 50%)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      }
    },
  },
  plugins: [],
}
