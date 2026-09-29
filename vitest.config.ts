import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      // Use the build of parquet-wasm that the browser bundle uses. Its Node
      // build is CommonJS inside an ES module package, which Node can't load.
      "parquet-wasm": "parquet-wasm/esm",
    },
  },
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
