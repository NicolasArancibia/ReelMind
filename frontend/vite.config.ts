import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const localServer = {
  host: '127.0.0.1', port: 5180, strictPort: true,
  proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: localServer,
  preview: localServer,
})
