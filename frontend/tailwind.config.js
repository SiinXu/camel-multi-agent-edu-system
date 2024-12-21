/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'neon-blue': '#00FFFF',
        'dark-bg': '#121212',
        // ... 其他自定义颜色
      },
      animation: {
        'glow': 'glow 1s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          'from': {
            'box-shadow': '0 0 10px #00FFFF, 0 0 20px #00FFFF, 0 0 30px #00FFFF',
          },
          'to': {
            'box-shadow': '0 0 20px #00FFFF, 0 0 30px #00FFFF, 0 0 40px #00FFFF',
          },
        },
      },
    },
  },
  plugins: [],
}