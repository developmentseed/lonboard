// build.js
import esbuild from "esbuild";
import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: ["./src/point.tsx", "./src/linestring.tsx", "./src/polygon.tsx"],
  bundle: true,
  outdir: "deck_widget/static/",
  plugins: [wasmLoader()],
  format: "esm",
});
