import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: the SPA dev server forwards /api and /media to the Django backend
// (the Docker dev stack publishes it on host port 8100). Override with
// VITE_BACKEND when running Django elsewhere.
const BACKEND = process.env.VITE_BACKEND || "http://localhost:8100";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // In production Django serves index.html and WhiteNoise serves the hashed
  // assets under STATIC_URL (/static/), so built asset URLs must be prefixed
  // with /static/. The dev server keeps the root base.
  base: command === "build" ? "/static/" : "/",
  server: {
    port: 5173,
    proxy: {
      // No changeOrigin: keep the browser's Host header (localhost:5173) so
      // Django's ALLOWED_HOSTS check passes and generated absolute URLs stay
      // browser-reachable.
      "/api": { target: BACKEND },
      "/media": { target: BACKEND },
    },
  },
  build: { outDir: "dist" },
}));
