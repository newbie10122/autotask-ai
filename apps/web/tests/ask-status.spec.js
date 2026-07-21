const { test, expect } = require("@playwright/test");
const { startStaticServer, stopStaticServer, stubApi } = require("./helpers");

let server;
let pageUrl;

test.beforeAll(async () => {
  ({ server, pageUrl } = await startStaticServer());
});

test.afterAll(async () => {
  await stopStaticServer(server);
});

test("ask workflow shows running and timeout states clearly", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, {
    routeAuthRequired: true,
    user: { username: "tech", roles: ["Technician"] },
    askHandler: async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      return route.fulfill({
        status: 504,
        contentType: "application/json",
        body: JSON.stringify({ detail: "timeout" })
      });
    }
  });
  await page.goto(`${pageUrl}#ask`);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  await page.locator("#question").fill("The outlook says it's offline");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByRole("button", { name: "Asking" })).toBeDisabled();
  await expect(page.locator("#askStatus")).toContainText("Waiting for assistant response");
  await expect(page.locator("#confidence")).toHaveText("Confidence: Pending");

  await expect(page.locator("#askStatus")).toContainText("timed out");
  await expect(page.getByRole("button", { name: "Ask", exact: true })).toBeEnabled();
  await expect(page.locator("#warnings")).toContainText("proxy timed out");
  await expect(page.locator("#confidence")).toHaveText("Confidence: None");
});
