import { defineConfig, ViteDevServer, PluginOption } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import type { IncomingMessage, ServerResponse } from 'http';

function supportPortalHtmlRewritePlugin(): PluginOption {
  return {
    name: 'support-portal-html-rewrite',
    configureServer(server: ViteDevServer) {
      server.middlewares.use((req: IncomingMessage, res: ServerResponse, next: any) => {
        if (req.url === '/' || req.url === '/customer-support.html') {
          req.url = '/customer-support.html';
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), supportPortalHtmlRewritePlugin()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      react: path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
    },
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    port: 5200,
    watch: { usePolling: true },
    proxy: {
      '/api': {
        target: process.env.PROXY_TARGET || 'http://localhost:6050',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      '/support': {
        target: process.env.PROXY_TARGET || 'http://localhost:6050',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: process.env.PROXY_TARGET || 'http://localhost:6050',
        changeOrigin: true,
        secure: false,
      },
    },
    open: false,
    fs: { allow: ['.'] },
  },
  build: {
    outDir: 'dist-support',
    assetsDir: 'assets',
    minify: 'terser',
    rollupOptions: {
      input: {
        supportPortal: path.resolve(__dirname, 'customer-support.html'),
      },
    },
  },
}); 
