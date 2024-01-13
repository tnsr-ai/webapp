import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://127.0.0.1:3000",
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    env: {
      backend: "http://127.0.0.1:8000",
    },
  },
  defaultCommandTimeout: 60000,
});
