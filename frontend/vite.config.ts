import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** В Docker Desktop: VITE_API_PROXY=http://host.docker.internal:8000 */
const apiProxy = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    fs: { allow: [".."] },
    proxy: {
      "/api": {
        target: apiProxy,
        changeOrigin: true,
      },
    },
  },
});
