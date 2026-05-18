import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4566',
        rewrite: path => path.replace(/^\/api/, ''),
        changeOrigin: true,
        // Forward all headers as-is; don't let Vite mangle them
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.error('[proxy error]', err.message)
          })
          proxy.on('proxyReq', (proxyReq) => {
            // MiniStack expects Host: localhost:4566
            proxyReq.setHeader('host', 'localhost:4566')
          })
        },
      },
    },
  },
})
