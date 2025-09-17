import { defineConfig } from 'vite'
import Vue from '@vitejs/plugin-vue'
import viteBasicSslPlugin from '@vitejs/plugin-basic-ssl'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import Components from 'unplugin-vue-components/vite'

// https://vitejs.dev/config/
export default defineConfig({
  base: '',
  server: {
    port: 3002,
    https: true,
    host: "0.0.0.0",
    proxy: {
      '/api': {
        target: 'https://gate.dataloop.ai/api',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  optimizeDeps: {
    include: [
      'lodash',
      'pdfjs-dist',
      'highlight.js',
      'flat',
      'three',
      'three/examples/jsm/controls/OrbitControls',
      'three/examples/jsm/loaders/GLTFLoader',
      'three/examples/jsm/loaders/OBJLoader',
      'three/examples/jsm/loaders/STLLoader',
      'three/examples/jsm/loaders/PLYLoader',
      'three/examples/jsm/loaders/FBXLoader',
      'three/examples/jsm/loaders/TDSLoader'
    ],
    exclude: ['node_modules', './node_modules', 'dist', './dist']
  },
  plugins: [
    Vue(),
    viteBasicSslPlugin(),
    Components({ resolvers: [IconsResolver()] }),
    Icons(),
  ],
  build: {
    outDir: 'panels/preview',
    // other build options
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'pdfjs-dist'],
          // other chunk definitions
        },
      },
    },
  },
})

