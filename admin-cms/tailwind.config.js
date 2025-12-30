/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'fraction-red': '#EF4444',
        'fraction-red-dark': '#DC2626',
        'fraction-yellow': '#FDE047',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Space Grotesk', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  safelist: [
    // Color utilities for dynamic classes
    'bg-blue-100', 'bg-purple-100', 'bg-green-100', 'bg-yellow-100', 'bg-red-100',
    'text-blue-600', 'text-purple-600', 'text-green-600', 'text-yellow-600', 'text-red-600',
    'bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500',
  ],
  plugins: [],
}
