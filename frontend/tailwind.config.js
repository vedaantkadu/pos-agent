export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        producer: {
          light: '#FF6B6B',
          DEFAULT: '#FF5252',
          dark: '#E63946',
        },
        administrator: {
          light: '#4ECDC4',
          DEFAULT: '#2A9D8F',
          dark: '#1B7A6E',
        },
        entrepreneur: {
          light: '#FFE66D',
          DEFAULT: '#FFB800',
          dark: '#F77F00',
        },
        integrator: {
          light: '#95E1D3',
          DEFAULT: '#06D6A0',
          dark: '#05B387',
        },
      },
    },
  },
  plugins: [],
}