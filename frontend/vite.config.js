// vite.config.js
//
// Minimal Vite config. Kept deliberately small: this project doesn't need
// a framework (React/Vue) for a Three.js scene, so the config stays close
// to Vite's defaults rather than accumulating plugins speculatively.

import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  server: {
    port: 5173,
    // Proxy not used yet — the SimulationClient connects directly to the
    // backend's WebSocket port (see src/config/constants.js). Revisit if
    // CORS/proxying becomes necessary for a production deployment.
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
