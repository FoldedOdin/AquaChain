/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        safe: '#10b981',
        warning: '#f59e0b',
        critical: '#ef4444',
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [],
}