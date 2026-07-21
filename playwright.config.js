const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "apps/web/tests",
  timeout: 30000,
  use: {
    browserName: "chromium",
    headless: true
  }
});
