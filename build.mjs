// build.js
import esbuild from "esbuild";
import { wasmLoader } from "esbuild-plugin-wasm";

esbuild.build({
  entryPoints: ["./src/index.tsx"],
  bundle: true,
  outdir: "deck_widget/static/",
  plugins: [wasmLoader()],
  format: "esm",
});
