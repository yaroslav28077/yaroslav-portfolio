import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

import { seo } from './vite-seo.ts'

// base './' — зібраний сайт відкривається з будь-якої теки й не прив'язаний до домену
export default defineConfig({
  base: './',
  plugins: [react(), seo()],
  // 3D-модуль (three + R3F) — окремий lazy chunk, тому ліміт попередження піднято лише для нього
  build: { target: 'es2022', sourcemap: false, chunkSizeWarningLimit: 1000 },
})
