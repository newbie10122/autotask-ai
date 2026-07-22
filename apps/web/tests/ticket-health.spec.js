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

test("ticket health view shows predictive ranking and abstention evidence", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, {
    routeAuthRequired: true,
    user: { username: "tech", roles: ["Technician"] },
    ticketDetailHandler: async (route) => route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        ticket: {
          ticket_number: "T20260421.0014",
          title: "Printer offline again",
          status_label: "New",
          priority_label: "High",
          queue_label: "Help Desk",
          assigned_resource_name: "Alex",
          health_score: 99,
          risk_bucket: "critical"
        },
        status_duration_summary: { current_status: "New", current_duration_hours: 12 },
        transitions: [],
        history_events: [],
        labor_entries: [],
        warnings: []
      })
    })
  });

  await page.goto(`${pageUrl}#ticket-health`);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  await expect(page.locator("#ticketReviewCandidates")).toHaveText("2");
  await expect(page.locator("#ticketPredictiveRanked")).toHaveText("1");
  await expect(page.locator("#ticketPredictiveAbstentions")).toHaveText("1");
  await expect(page.locator("#ticketHealthGuidance")).toContainText("review-only");

  const queue = page.locator("#ticketHealthReviewQueue");
  await expect(queue).toContainText("T20260421.0014");
  await expect(queue).toContainText("strong");
  await expect(queue).toContainText("5980");
  await expect(queue).toContainText("calibrated_delay_probability=0.56");
  await expect(queue).toContainText("Abstained");
  await expect(queue).toContainText("insufficient_local_history");

  await queue.getByRole("button", { name: "T20260421.0014" }).click();
  await expect(page.getByRole("dialog", { name: "Ticket T20260421.0014" })).toBeVisible();
});
