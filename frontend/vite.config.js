import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/captcha': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
    },
  },
})
