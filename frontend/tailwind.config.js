/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef9ff',
          100: '#d8f1ff',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        danger: '#dc3545',
        warning: '#ffc107',
        success: '#28a745',
        surface: {
          base: '#000000',
          raised: '#1c1c1e',
          overlay: '#2c2c2e',
          highlight: '#3a3a3c',
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
        '4xl': '1.5rem',
      },
      boxShadow: {
        'elevation-1': '0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)',
        'elevation-2': '0 4px 12px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3)',
        'elevation-3': '0 12px 40px rgba(0,0,0,0.6), 0 4px 12px rgba(0,0,0,0.4)',
        'brand-glow': '0 4px 20px rgba(14,165,233,0.25), 0 2px 8px rgba(14,165,233,0.15)',
        'inner-soft': 'inset 0 1px 3px rgba(0,0,0,0.4)',
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%)',
        'gradient-card': 'linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 100%)',
      },
      fontSize: {
        'body': ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.4' }],
        'caption': ['0.75rem', { lineHeight: '1.3' }],
        'heading-sm': ['1.25rem', { lineHeight: '1.3' }],
        'heading-md': ['1.5rem', { lineHeight: '1.2' }],
        'heading-lg': ['1.75rem', { lineHeight: '1.2' }],
      },
      keyframes: {
        press: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(0.97)' },
          '100%': { transform: 'scale(1)' },
        },
        pageEnter: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-100% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'press': 'press 0.15s ease-out',
        'page-enter': 'pageEnter 0.3s cubic-bezier(0.16, 1, 0.3, 1) both',
        'shimmer': 'shimmer 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
