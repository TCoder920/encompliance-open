// Tailwind config for v3.4.1. Custom utilities and font families are defined here.
// If upgrading to Tailwind v4, see the README for required changes.
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'navy-blue': '#003366',
        'dark-bg': '#121212',
        'dark-surface': '#1e1e1e',
        'dark-border': '#333333',
        'dark-text': '#e0e0e0',
      },
      fontFamily: {
        'arial': ['Arial', 'Helvetica', 'sans-serif'],
        'times': ['"Times New Roman"', 'Times', 'serif'],
      },
      animation: {
        'theme-transition': 'themeTransition 2s ease-in-out',
        'marquee': 'marquee 25s linear infinite',
        'marquee2': 'marquee2 25s linear infinite',
        'morphing-cloud': 'morphingCloud 8s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        'water-pulse': 'waterPulse 2.5s ease-in-out infinite',
        'water-ripple': 'waterRipple 2.5s ease-in-out infinite',
        'water-ripple-delay': 'waterRipple 2.5s ease-in-out 0.8s infinite',
        'water-ripple-delay2': 'waterRipple 2.5s ease-in-out 1.6s infinite',
        'fadeIn': 'fadeIn 0.3s ease-in',
        'fadeOut': 'fadeOut 0.5s ease-out forwards',
      },
      keyframes: {
        themeTransition: {
          '0%': { opacity: '1' },
          '50%': { opacity: '0.7' },
          '100%': { opacity: '1' },
        },
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        marquee2: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0%)' },
        },
        morphingCloud: {
          '0%': { borderRadius: '60% 40% 30% 70%/60% 30% 70% 40%' },
          '50%': { borderRadius: '30% 60% 70% 40%/50% 60% 30% 60%' },
          '100%': { borderRadius: '60% 40% 30% 70%/60% 30% 70% 40%' },
        },
        pulseGlow: {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' },
          '100%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.5)' },
        },
        waterPulse: {
          '0%': { transform: 'scale(0.95)', opacity: '0.8' },
          '25%': { transform: 'scale(1.05)', opacity: '1' },
          '50%': { transform: 'scale(0.98)', opacity: '0.9' },
          '75%': { transform: 'scale(1.02)', opacity: '1' },
          '100%': { transform: 'scale(0.95)', opacity: '0.8' },
        },
        waterRipple: {
          '0%': { transform: 'scale(0.8)', opacity: '0.8' },
          '50%': { transform: 'scale(1.5)', opacity: '0' },
          '100%': { transform: 'scale(0.8)', opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};