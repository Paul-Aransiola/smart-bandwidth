import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      scss: {
        // Suppress deprecation warnings for @import (legacy SCSS compatibility)
        api: 'modern-compiler',
        silenceDeprecations: ['import', 'legacy-js-api']
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.DOCKER_ENV ? 'http://api:8000' : 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
