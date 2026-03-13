/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base:    '#0d1117',
        surface: '#161b22',
        raised:  '#1c2128',
        hover:   '#21262d',
        border:  '#30363d',
        'text-hi':  '#e6edf3',
        'text-lo':  '#8b949e',
        'text-dim': '#6e7681',
        'col-blue':  '#1f6feb',
        'col-green': '#3fb950',
        'col-amber': '#d29922',
        'col-red':   '#f85149',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
