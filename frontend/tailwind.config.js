/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'pipeline': {
          'dark': '#0a0e1a',
          'darker': '#060810',
          'card': '#111827',
          'border': '#1f2937',
          'accent': '#10b981',
          'warning': '#f59e0b',
          'danger': '#ef4444',
          'critical': '#dc2626',
          'safe': '#22c55e',
          'neon-green': '#39ff14',
          'neon-blue': '#00d4ff',
        }
      },
      backdropBlur: {
        'glass': '16px',
      },
      boxShadow: {
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.3)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.3)',
        'glow-yellow': '0 0 20px rgba(245, 158, 11, 0.3)',
      }
    },
  },
  plugins: [],
}
