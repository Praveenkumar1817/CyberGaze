/**
 * tailwind.config.js — Tailwind CSS Configuration for CyberGaze Dashboard
 * Dark cybersecurity theme with neon accent colors.
 */
/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            colors: {
                cyber: {
                    bg: '#080c14',
                    surface: '#0f1724',
                    card: '#141e2e',
                    border: '#1e3a5f',
                    accent: '#00d4ff',
                    green: '#00ff88',
                    red: '#ff3366',
                    orange: '#ff7733',
                    yellow: '#ffd700',
                    purple: '#a855f7',
                }
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px #ff3366, 0 0 10px #ff3366' },
                    '100%': { boxShadow: '0 0 20px #ff3366, 0 0 40px #ff3366, 0 0 60px #ff3366' },
                }
            }
        },
    },
    plugins: [],
}
