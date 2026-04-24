import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true, // Включает polling для отслеживания изменений
      interval: 1000    // Проверять изменения каждую секунду (можно уменьшить до 500)
    },
  },
})