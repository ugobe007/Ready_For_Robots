/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Readability lift on #080808 background.
        // Only 500 and 600 are remapped — borders/backgrounds (700-950) unchanged.
        // neutral-500: #737373 (4.3:1) → #8f8f8f (5.8:1)  — passes WCAG AA
        // neutral-600: #525252 (2.8:1) → #6b6b6b (4.0:1)  — near-AA (labels, meta)
        neutral: {
          50:  '#fafafa',
          100: '#f5f5f5',
          200: '#e5e5e5',
          300: '#d4d4d4',
          400: '#a3a3a3',
          500: '#8f8f8f',
          600: '#6b6b6b',
          700: '#404040',
          800: '#262626',
          900: '#171717',
          950: '#0a0a0a',
        },
      },
    },
  },
  plugins: [],
};
