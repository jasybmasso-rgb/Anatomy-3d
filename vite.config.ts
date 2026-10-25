import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { anatomyPwa } from "./scripts/anatomyPwa";

const base = process.env.VITE_BASE || "/";

export default defineConfig({
  base,
  plugins: [react(), anatomyPwa()],
  server: {
    host: true,
    port: 5173,
  },
});
