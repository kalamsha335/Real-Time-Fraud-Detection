/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          950: 'var(--bg-app)',
          900: 'var(--bg-card)',
          850: 'var(--bg-card-hover)',
          800: 'var(--bg-surface)',
          700: 'var(--border-color)',
          600: 'var(--border-hover)'
        },
        navy: {
          950: 'var(--bg-app)',
          900: 'var(--bg-card)',
          850: 'var(--bg-card-hover)',
          800: 'var(--bg-surface)',
          700: 'var(--border-color)',
          600: 'var(--border-hover)'
        },
        brand: {
          blue: '#2563EB',
          indigo: '#4F46E5',
          violet: '#7C3AED',
          sky: '#0284C7'
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#F43F5E',
          info: '#3B82F6'
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace']
      }
    },
  },
  plugins: [],
}
