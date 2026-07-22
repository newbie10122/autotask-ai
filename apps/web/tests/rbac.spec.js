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

test("anonymous browser state fails closed when app route auth is required", async ({ page }) => {
  await stubApi(page, { routeAuthRequired: true });
  await page.goto(pageUrl);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");
  await expect(page.locator("#pauseOperations")).toBeDisabled();
  await expect(page.locator("[data-action='/api/sync/reference-data/start']")).toBeDisabled();
  await expect(page.locator("[data-rating='Good']")).toBeDisabled();
});

test("admin browser state enables admin and technician controls", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, { routeAuthRequired: true, user: { username: "admin", roles: ["Admin"] } });
  await page.goto(pageUrl);
  await expect(page.locator("#authStatus")).toContainText("admin: Admin");
  await expect(page.locator("#referenceSources")).toHaveText("bootstrap: 1 / inferred: 2");
  await expect(page.locator("#pauseOperations")).toBeEnabled();
  await expect(page.locator("[data-action='/api/sync/reference-data/start']")).toBeEnabled();
  await expect(page.locator("[data-rating='Good']")).toBeEnabled();
});

test("readonly browser state keeps privileged controls disabled", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, { routeAuthRequired: true, user: { username: "reader", roles: ["ReadOnly"] } });
  await page.goto(pageUrl);
  await expect(page.locator("#authStatus")).toContainText("reader: ReadOnly");
  await expect(page.locator("#pauseOperations")).toBeDisabled();
  await expect(page.locator("[data-action='/api/sync/reference-data/start']")).toBeDisabled();
  await expect(page.locator("[data-rating='Good']")).toBeDisabled();
});
