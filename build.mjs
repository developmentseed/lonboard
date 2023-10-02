// build.js
import esbuild from "esbuild";
// import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: [
    "./src/index.tsx",
    "./src/point.tsx",
    "./src/linestring.tsx",
    "./src/polygon.tsx",
    "./src/polygon-layer.ts",
  ],
  bundle: true,
  minify: true,
  target: ["es2020"],
  outdir: "lonboard/static/",
  // plugins: [wasmLoader()],
  format: "esm",
});
