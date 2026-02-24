import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration for CyberGaze Dashboard
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API calls to avoid CORS issues in dev (optional backup to explicit CORS headers)
    proxy: {
      '/api/ai': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/ai/, ''),
      },
    },
  },
})
