const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;
const { startStaticServer, stopStaticServer, stubApi } = require("./helpers");

let server;
let pageUrl;

test.beforeAll(async () => {
  ({ server, pageUrl } = await startStaticServer());
});

test.afterAll(async () => {
  await stopStaticServer(server);
});

test("dashboard has no serious or critical accessibility violations", async ({ page }) => {
  await stubApi(page, { routeAuthRequired: true, user: { username: "admin", roles: ["Admin"] } });
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await page.goto(pageUrl);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  const results = await new AxeBuilder({ page }).analyze();
  const seriousViolations = results.violations.filter((violation) => ["serious", "critical"].includes(violation.impact));

  expect(seriousViolations).toEqual([]);
});

test("login controls expose accessible names in the browser", async ({ page }) => {
  await stubApi(page, { routeAuthRequired: true });
  await page.goto(pageUrl);

  await expect(page.getByLabel("Username")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
  await expect(page.getByRole("navigation")).toBeVisible();
});
