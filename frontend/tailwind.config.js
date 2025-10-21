/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // AquaChain Brand Colors
        aqua: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#06b6d4', // Primary
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },
        teal: {
          500: '#088395', // Secondary
          600: '#0f766e',
        },
        emerald: {
          400: '#1de9b6', // Accent
        },
        // Legacy colors for existing components
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
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'bubble-rise': 'bubble-rise 12s linear infinite',
        'caustics': 'caustics-flow 15s ease-in-out infinite',
        'gentle-wave': 'gentle-wave 20s ease-in-out infinite',
        'typewriter': 'typewriter 3s steps(40) 1s forwards',
        'blink': 'blink 1s infinite',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        'bubble-rise': {
          '0%': { transform: 'translateY(100vh) scale(1)', opacity: '0' },
          '10%': { opacity: '1' },
          '90%': { opacity: '0.8' },
          '100%': { transform: 'translateY(-100px) scale(0.3)', opacity: '0' }
        },
        'caustics-flow': {
          '0%, 100%': { transform: 'translateX(-50%) translateY(-50%) rotate(0deg)' },
          '50%': { transform: 'translateX(-50%) translateY(-50%) rotate(180deg)' }
        },
        'gentle-wave': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' }
        },
        'typewriter': {
          '0%': { width: '0' },
          '100%': { width: '100%' }
        },
        'blink': {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' }
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        }
      },
      boxShadow: {
        'underwater': '0 0 50px rgba(6, 182, 212, 0.3), 0 0 100px rgba(6, 182, 212, 0.1)',
        'glow': '0 0 20px rgba(6, 182, 212, 0.5)',
      },
      zIndex: {
        'hide': '-1',
        'auto': 'auto',
        'base': '0',
        'docked': '10',
        'dropdown': '1000',
        'sticky': '1100',
        'banner': '1200',
        'overlay': '1300',
        'modal': '1400',
        'popover': '1500',
        'skip-link': '1600',
        'toast': '1700',
        'tooltip': '1800',
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [],
}