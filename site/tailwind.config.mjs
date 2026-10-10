/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#2478FF',
          light: 'rgb(var(--brand-light) / <alpha-value>)',
          dark: '#1a5fd0',
        },
        accent: {
          DEFAULT: '#9254FF',
          light: '#a874ff',
        },
        ink: {
          DEFAULT: 'rgb(var(--ink) / <alpha-value>)',
          card: 'rgb(var(--ink-card) / <alpha-value>)',
          border: 'rgb(var(--ink-border) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: {
        prose: '56rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(18px)' },
          '100%': { opacity: '1', transform: 'none' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.9)', opacity: '0.6' },
          '100%': { transform: 'scale(1.6)', opacity: '0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s ease both',
        float: 'float 7s ease-in-out infinite',
        'pulse-ring': 'pulse-ring 3s ease-out infinite',
      },
    },
  },
  plugins: [],
};
