import { defineConfig } from "vite";
export default defineConfig({
  base: "/github-learning-site/",
  server: { host: "127.0.0.1" },
  build: { target: "es2022" },
});
