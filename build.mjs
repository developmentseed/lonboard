// build.js
import esbuild from "esbuild";
// import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: [
    "./src/index.tsx",
    "./src/scatterplot-layer.tsx",
    "./src/path-layer.tsx",
    "./src/solid-polygon-layer.tsx",
  ],
  bundle: true,
  minify: false,
  target: ["es2020"],
  outdir: "lonboard/static/",
  // plugins: [wasmLoader()],
  format: "esm",
});
