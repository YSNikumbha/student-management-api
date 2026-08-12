import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": new URL("./src", import.meta.url).pathname,
    },
  },
  server: {
    host: "0.0.0.0",
    port: Number.parseInt(process.env.PORT || "5173", 10),
  },
  preview: {
    host: "0.0.0.0",
    port: Number.parseInt(process.env.PORT || "5173", 10),
  },
});
