// build.js
import esbuild from "esbuild";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

// List of environment variables to expose to the build
const env = {
  "process.env.XSTATE_INSPECT": JSON.stringify(process.env.XSTATE_INSPECT),
};

esbuild.build({
  entryPoints: ["./src/index.tsx"],
  bundle: true,
  minify: true,
  target: ["es2022"],
  outdir: "lonboard/static/",
  format: "esm",
  // Ref https://github.com/manzt/anywidget/issues/369#issuecomment-1792376003
  define: {
    "define.amd": "false",
    ...env,
  },
  // Code splitting didn't work initially because it tried to load from a local
  // relative path ./chunk.js
  // splitting: true,
});
