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

test("operations view surfaces scheduler and related-data automation movement", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, {
    routeAuthRequired: true,
    user: { username: "admin", roles: ["Admin"] }
  });

  await page.goto(`${pageUrl}#operations`);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  await expect(page.locator("#opsTimeEntries")).toHaveText("49054");
  await expect(page.locator("#opsTicketHistory")).toHaveText("29340");
  await expect(page.locator("#schedulerState")).toHaveText("healthy");
  await expect(page.locator("#schedulerHeartbeat")).toHaveText("12s ago");
  await expect(page.locator("#schedulerNextDue")).toContainText("open_ticket_history_gaps");

  const automationPanel = page.locator("#relatedDataAutomation");
  await expect(automationPanel).toContainText("open_ticket_history_gaps");
  await expect(automationPanel).toContainText("ticket_time_entry_gaps");
  await expect(automationPanel).toContainText("685");
  await expect(automationPanel).toContainText("40");
  await expect(automationPanel).toContainText("None");
});
