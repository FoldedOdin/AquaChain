/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Aqua Brand
        aqua: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#06b6d4', // Primary brand color
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },
        
        // Water Quality Status
        'wq-excellent': '#10b981',
        'wq-good': '#06b6d4',
        'wq-fair': '#f59e0b',
        'wq-poor': '#ef4444',
        'wq-critical': '#dc2626',
        
        // Role-specific colors
        admin: {
          primary: '#8b5cf6',
          secondary: '#a78bfa',
          accent: '#c4b5fd',
        },
        field: {
          primary: '#06b6d4',
          secondary: '#22d3ee',
          accent: '#67e8f9',
        },
        lab: {
          primary: '#10b981',
          secondary: '#34d399',
          accent: '#6ee7b7',
        },
        audit: {
          primary: '#6366f1',
          secondary: '#818cf8',
          accent: '#a5b4fc',
        },

        // Legacy colors for existing components
        teal: {
          500: '#088395', // Secondary
          600: '#0f766e',
        },
        emerald: {
          400: '#1de9b6', // Accent
        },
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
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        display: ['Poppins', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
      fontFeatureSettings: {
        numeric: ['tnum', 'zero'], // Tabular numbers
      },
      keyframes: {
        // Water-themed animations
        'bubble-rise': {
          '0%': {
            transform: 'translateY(0) scale(1)',
            opacity: '0.7'
          },
          '50%': {
            transform: 'translateY(-50px) scale(1.1)',
            opacity: '0.5'
          },
          '100%': {
            transform: 'translateY(-100px) scale(0.8)',
            opacity: '0'
          },
        },
        'caustics-flow': {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
            opacity: '0.3'
          },
          '50%': {
            backgroundPosition: '100% 50%',
            opacity: '0.5'
          },
        },
        'gentle-wave': {
          '0%, 100%': { transform: 'translateX(0) translateY(0)' },
          '25%': { transform: 'translateX(5px) translateY(-5px)' },
          '50%': { transform: 'translateX(0) translateY(-10px)' },
          '75%': { transform: 'translateX(-5px) translateY(-5px)' },
        },
        
        // UI animations
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-in-right': {
          '0%': {
            transform: 'translateX(100%)',
            opacity: '0'
          },
          '100%': {
            transform: 'translateX(0)',
            opacity: '1'
          },
        },
        'slide-up': {
          '0%': {
            transform: 'translateY(10px)',
            opacity: '0'
          },
          '100%': {
            transform: 'translateY(0)',
            opacity: '1'
          },
        },
        'scale-in': {
          '0%': {
            transform: 'scale(0.9)',
            opacity: '0'
          },
          '100%': {
            transform: 'scale(1)',
            opacity: '1'
          },
        },
        
        // Data animations
        'data-update': {
          '0%': {
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            transform: 'scale(1)'
          },
          '50%': {
            backgroundColor: 'rgba(6, 182, 212, 0.3)',
            transform: 'scale(1.02)'
          },
          '100%': {
            backgroundColor: 'transparent',
            transform: 'scale(1)'
          },
        },
        'number-pop': {
          '0%': {
            transform: 'scale(0.8)',
            opacity: '0'
          },
          '100%': {
            transform: 'scale(1)',
            opacity: '1'
          },
        },
        
        // Chart animations
        'line-draw': {
          'to': { strokeDashoffset: '0' },
        },
        'bar-grow': {
          'from': {
            transform: 'scaleY(0)',
            transformOrigin: 'bottom'
          },
          'to': { transform: 'scaleY(1)' },
        },
        
        // Loading animations
        'pulse-slow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        
        // Interactive animations
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'wiggle': {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        
        // Status animations
        'badge-glow': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(16, 185, 129, 0.7)' },
          '50%': { boxShadow: '0 0 0 8px rgba(16, 185, 129, 0)' },
        },
        'alert-pulse': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.7)' },
          '50%': { boxShadow: '0 0 0 12px rgba(239, 68, 68, 0)' },
        },

        // Legacy animations
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
      animation: {
        // Water effects
        'bubble-rise': 'bubble-rise 4s ease-in-out infinite',
        'caustics-flow': 'caustics-flow 8s ease-in-out infinite',
        'gentle-wave': 'gentle-wave 3s ease-in-out infinite',
        
        // UI
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in-right': 'slide-in-right 0.4s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
        
        // Data
        'data-update': 'data-update 0.8s ease-out',
        'number-pop': 'number-pop 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        
        // Charts
        'line-draw': 'line-draw 1.5s ease-out forwards',
        'bar-grow': 'bar-grow 0.6s ease-out',
        
        // Loading
        'pulse-slow': 'pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-subtle': 'pulse-subtle 3s ease-in-out infinite',
        
        // Interactive
        'float': 'float 3s ease-in-out infinite',
        'wiggle': 'wiggle 0.5s ease-in-out infinite',
        'bounce-subtle': 'bounce-subtle 2s ease-in-out infinite',
        
        // Status
        'badge-glow': 'badge-glow 2s ease-in-out infinite',
        'alert-pulse': 'alert-pulse 2s ease-in-out infinite',

        // Legacy
        'typewriter': 'typewriter 3s steps(40) 1s forwards',
        'blink': 'blink 1s infinite',
        'shimmer': 'shimmer 2s infinite',
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