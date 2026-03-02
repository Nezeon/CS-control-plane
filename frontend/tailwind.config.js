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
        bg: {
          DEFAULT: '#09090B',
          subtle: '#111113',
          elevated: '#18181B',
          active: '#27272A',
        },
        border: {
          DEFAULT: '#27272A',
          strong: '#3F3F46',
          subtle: '#1C1C1E',
        },
        accent: {
          DEFAULT: '#6366F1',
          hover: '#818CF8',
          muted: '#4338CA',
          subtle: 'rgba(99, 102, 241, 0.12)',
        },
        data: {
          DEFAULT: '#06B6D4',
          hover: '#22D3EE',
          muted: '#0891B2',
          subtle: 'rgba(6, 182, 212, 0.12)',
        },
        status: {
          success: '#22C55E',
          warning: '#EAB308',
          danger: '#EF4444',
          info: '#6366F1',
        },
        text: {
          primary: '#FAFAFA',
          secondary: '#A1A1AA',
          muted: '#71717A',
          ghost: '#52525B',
          accent: '#6366F1',
        },
        severity: {
          p1: '#EF4444',
          p2: '#EAB308',
          p3: '#06B6D4',
          p4: '#71717A',
        },
        lane: {
          control: '#6366F1',
          value: '#22C55E',
          support: '#EAB308',
          delivery: '#06B6D4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'xxs': ['0.6875rem', { lineHeight: '1rem' }],
        'xs':  ['0.8125rem', { lineHeight: '1.25rem' }],
        'sm':  ['0.875rem',  { lineHeight: '1.375rem' }],
        'base':['0.9375rem', { lineHeight: '1.5rem' }],
        'lg':  ['1.125rem',  { lineHeight: '1.625rem' }],
        'xl':  ['1.375rem',  { lineHeight: '1.75rem' }],
        '2xl': ['1.75rem',   { lineHeight: '2.25rem' }],
        '3xl': ['2.25rem',   { lineHeight: '2.75rem' }],
      },
      borderRadius: {
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      spacing: {
        18: '4.5rem',
        88: '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-up': 'slideInUp 0.3s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
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
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}
