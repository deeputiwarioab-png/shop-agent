import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    cssInjectedByJsPlugin(), // Injects CSS into the JS bundle
  ],
  build: {
    lib: {
      entry: 'src/main.tsx',
      name: 'ShopAgentWidget',
      fileName: (format) => `bundle.js`,
      formats: ['iife'], // Immediately Invoked Function Expression for direct script tag usage
    },
    rollupOptions: {
      output: {
        // Ensure we don't get a separate CSS file if possible, or handle it via the plugin
        manualChunks: undefined,
      },
    },
  },
  define: {
    'process.env': {
      NODE_ENV: JSON.stringify('production'),
    }
  }
})
