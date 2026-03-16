import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    path.join(__dirname, 'index.html'),
    path.join(__dirname, 'src/**/*.{js,ts,jsx,tsx}'),
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds — layered depth
        void: '#050507',
        bg: {
          DEFAULT: '#050507',
          subtle: '#0C0D10',
          card: '#12131A',
          hover: '#1A1B24',
          active: '#222330',
        },
        // Borders
        border: {
          DEFAULT: '#222438',
          subtle: '#181A24',
          strong: '#2E3048',
        },
        // Primary — Electric Violet
        accent: {
          DEFAULT: '#7C5CFC',
          hover: '#9B7FFF',
          muted: '#5B3FD9',
          glow: 'rgba(124, 92, 252, 0.15)',
          subtle: 'rgba(124, 92, 252, 0.08)',
        },
        // Secondary — Vivid Teal
        teal: {
          DEFAULT: '#00E5C4',
          hover: '#33FFE0',
          muted: '#00B89E',
          glow: 'rgba(0, 229, 196, 0.15)',
          subtle: 'rgba(0, 229, 196, 0.08)',
        },
        // Tertiary — Sky Blue
        sky: {
          DEFAULT: '#3B9EFF',
          muted: '#2B7BD4',
          glow: 'rgba(59, 158, 255, 0.15)',
          subtle: 'rgba(59, 158, 255, 0.08)',
        },
        // Text
        text: {
          primary: '#EDEDF0',
          secondary: '#8F8FA3',
          muted: '#5C5C72',
          ghost: '#3E3E52',
        },
        // Status
        status: {
          success: '#00E5A0',
          warning: '#FFB547',
          danger: '#FF5C5C',
          info: '#7C5CFC',
        },
        // Severity
        severity: {
          p1: '#FF5C5C',
          p2: '#FFB547',
          p3: '#3B9EFF',
          p4: '#5C5C72',
        },
        // Tier colors
        tier: {
          1: '#7C5CFC',
          2: '#3B9EFF',
          3: '#00E5C4',
          4: '#5C5C72',
        },
        // Lane colors
        lane: {
          control: '#7C5CFC',
          support: '#FFB547',
          value: '#00E5A0',
          delivery: '#3B9EFF',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'xxs': ['0.6875rem', { lineHeight: '1rem' }],
        'xs':  ['0.75rem',   { lineHeight: '1.125rem' }],
        'sm':  ['0.8125rem', { lineHeight: '1.25rem' }],
        'base':['0.875rem',  { lineHeight: '1.375rem' }],
        'lg':  ['1rem',      { lineHeight: '1.5rem' }],
        'xl':  ['1.25rem',   { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem',    { lineHeight: '2rem' }],
        '3xl': ['2rem',      { lineHeight: '2.5rem' }],
        '4xl': ['2.5rem',    { lineHeight: '3rem' }],
      },
      borderRadius: {
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
      },
      spacing: {
        18: '4.5rem',
        88: '22rem',
      },
      backdropBlur: {
        xs: '4px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in-up': 'slideInUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in-left': 'slideInLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.8s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
        'connection-flow': 'connectionFlow 1.5s linear infinite',
        'connection-glow': 'connectionGlow 2s ease-in-out infinite',
        'pulse-ring': 'pulseRing 2s ease-in-out infinite',
        'ticker': 'tickerScroll 30s linear infinite',
        'scanline': 'scanline 4s linear infinite',
        'cursor-blink': 'cursorBlink 1s step-end infinite',
        'gradient-shift': 'gradientShift 4s ease infinite',
        'breathe-glow': 'breatheGlow 2s ease-in-out infinite',
        'idle-ring': 'idleRing 2.5s ease-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(124, 92, 252, 0)' },
          '50%': { boxShadow: '0 0 16px 4px rgba(124, 92, 252, 0.2)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        breathe: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        connectionFlow: {
          '0%': { strokeDashoffset: '24' },
          '100%': { strokeDashoffset: '0' },
        },
        connectionGlow: {
          '0%, 100%': { opacity: '0.1' },
          '50%': { opacity: '0.3' },
        },
        pulseRing: {
          '0%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '0', transform: 'scale(1.05)' },
          '100%': { opacity: '0', transform: 'scale(1.05)' },
        },
        tickerScroll: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        scanline: {
          '0%': { top: '0', opacity: '0.3' },
          '50%': { opacity: '0.15' },
          '100%': { top: '100%', opacity: '0' },
        },
        cursorBlink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        breatheGlow: {
          '0%, 100%': { opacity: '0.4', textShadow: '0 0 4px rgba(124, 92, 252, 0.3)' },
          '50%': { opacity: '1', textShadow: '0 0 12px rgba(124, 92, 252, 0.5)' },
        },
        idleRing: {
          '0%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0', transform: 'scale(1.5)' },
          '100%': { opacity: '0', transform: 'scale(1.5)' },
        },
      },
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      boxShadow: {
        'glow-sm': '0 0 8px rgba(124, 92, 252, 0.15)',
        'glow-md': '0 0 16px rgba(124, 92, 252, 0.2)',
        'glow-lg': '0 0 32px rgba(124, 92, 252, 0.25)',
        'glow-teal': '0 0 16px rgba(0, 229, 196, 0.2)',
        'card': '0 0 0 1px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.2)',
        'card-hover': '0 0 0 1px rgba(124, 92, 252, 0.2), 0 12px 40px rgba(0,0,0,0.3)',
      },
    },
  },
  plugins: [],
}
