import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// server.* only affects `vite dev` (used by docker-compose.override.yml for hot reload);
// `vite build` ignores it entirely, so this has no effect on the production image.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      // Short-link redirects: mirrors proxy/nginx.conf's short-code location so `npm run dev`
      // behaves the same way as the full stack when a link in the table is clicked.
      '^/[A-Za-z0-9]{3,16}$': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
