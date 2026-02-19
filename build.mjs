import autoprefixer from "autoprefixer";
import dotenv from "dotenv";
import esbuild from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import postcss from "postcss";
import postcssPresetEnv from "postcss-preset-env";
import tailwindcss from "tailwindcss";

// Load environment variables from .env file
dotenv.config();

const node_env = process.env.NODE_ENV || "production";

// List of environment variables to expose to the build
const defineEnv = {
  // Ref https://github.com/manzt/anywidget/issues/369#issuecomment-1792376003
  "define.amd": "false",
  "process.env.NODE_ENV": JSON.stringify(node_env),
  "process.env.XSTATE_INSPECT": JSON.stringify(
    process.env.XSTATE_INSPECT || "false",
  ),
};

esbuild.build({
  entryPoints: ["./src/index.tsx"],
  outdir: "lonboard/static/",
  bundle: true,
  format: "esm",
  target: ["es2022"],
  // Build sourcemaps when not in prod
  sourcemap: node_env !== "production",
  // Minify only in prod
  minify: node_env === "production",
  define: defineEnv,
  plugins: [
    sassPlugin({
      async transform(source) {
        const { css } = await postcss([
          tailwindcss,
          autoprefixer,
          postcssPresetEnv({ stage: 0 }),
        ]).process(source, { from: undefined });
        return css;
      },
    }),
  ],
  // Force all packages (including those nested inside local file deps) to
  // resolve to lonboard's own copies, preventing duplicate instances.
  alias: {
    "@deck.gl/aggregation-layers": "./node_modules/@deck.gl/aggregation-layers",
    "@deck.gl/core": "./node_modules/@deck.gl/core",
    "@deck.gl/extensions": "./node_modules/@deck.gl/extensions",
    "@deck.gl/geo-layers": "./node_modules/@deck.gl/geo-layers",
    "@deck.gl/layers": "./node_modules/@deck.gl/layers",
    "@deck.gl/mapbox": "./node_modules/@deck.gl/mapbox",
    "@deck.gl/mesh-layers": "./node_modules/@deck.gl/mesh-layers",
    "@deck.gl/react": "./node_modules/@deck.gl/react",
    "@deck.gl/widgets": "./node_modules/@deck.gl/widgets",
    "@luma.gl/constants": "./node_modules/@luma.gl/constants",
    "@luma.gl/core": "./node_modules/@luma.gl/core",
    "@luma.gl/engine": "./node_modules/@luma.gl/engine",
    "@luma.gl/gltf": "./node_modules/@luma.gl/gltf",
    "@luma.gl/shadertools": "./node_modules/@luma.gl/shadertools",
    "@luma.gl/webgl": "./node_modules/@luma.gl/webgl",
  },
  platform: "browser",
  loader: {
    ".worker.js": "text",
    ".worker.min.js": "text",
  },
  // Code splitting didn't work initially because it tried to load from a local
  // relative path ./chunk.js
  // splitting: true,
});
