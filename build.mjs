// build.js
import esbuild from "esbuild";
// import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: [
    "./src/index.tsx",
  ],
  bundle: true,
  minify: true,
  target: ["es2020"],
  outdir: "lonboard/static/",
  // plugins: [wasmLoader()],
  format: "esm",
});
