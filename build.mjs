// build.js
import esbuild from "esbuild";
// import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: ["./src/point.tsx", "./src/linestring.tsx", "./src/polygon.tsx"],
  bundle: true,
  minify: true,
  target: ["es2020"],
  outdir: "lonboard/static/",
  // plugins: [wasmLoader()],
  format: "esm",
});
