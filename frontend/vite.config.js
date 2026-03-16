import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(async () => {
  const plugins = [react()]

  if (process.env.ANALYZE) {
    const { visualizer } = await import('rollup-plugin-visualizer')
    plugins.push(visualizer({ open: true, filename: 'dist/bundle-stats.html', gzipSize: true }))
  }

  return {
  plugins,
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          gsap: ['gsap'],
        },
      },
    },
  },
  css: {
    postcss: {
      plugins: [
        tailwindcss(path.join(__dirname, 'tailwind.config.js')),
        autoprefixer(),
      ],
    },
  },
  server: {
    port: parseInt(process.env.PORT) || 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  }
})
