/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        // We will define custom colors if needed, but Tailwind's default palette is good.
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
