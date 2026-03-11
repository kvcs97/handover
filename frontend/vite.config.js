import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') }
  },
  // Tauri: kein fixer Port in Prod nötig
  server: {
    port: 5173,
    strictPort: true,
  },
  // Tauri erwartet relative Pfade
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
