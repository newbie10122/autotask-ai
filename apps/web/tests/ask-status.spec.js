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

test("based-on ticket opens scoped ticket detail modal", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await stubApi(page, {
    routeAuthRequired: true,
    user: { username: "tech", roles: ["Technician"] },
    askHandler: async (route) => route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        answer_id: 42,
        answer: "Confidence: Medium\n\nSuggested Next Steps\n- Review ticket evidence.",
        confidence: "Medium",
        based_on_tickets: ["T20230715.0124"],
        warnings: []
      })
    }),
    ticketDetailHandler: async (route) => route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        ticket: {
          ticket_number: "T20230715.0124",
          title: "Outlook offline",
          status_label: "New",
          priority_label: "Normal",
          queue_label: "Help Desk",
          assigned_resource_name: "Alex",
          health_score: 78,
          risk_bucket: "watch"
        },
        status_duration_summary: {
          current_status: "New",
          current_duration_hours: 3.5
        },
        transitions: [{ to_status: "New" }],
        history_events: [{ happened_at: "2026-07-21T12:00:00Z", action: "Status Changed", detail: "Created as New" }],
        labor_entries: [{ created_at_autotask: "2026-07-21T12:15:00Z", resource_name: "Alex", hours: 0.5, summary: "Initial triage" }],
        warnings: ["Review before applying a fix."]
      })
    })
  });
  await page.goto(`${pageUrl}#ask`);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  await page.locator("#question").fill("The outlook says it's offline");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.locator("#askStatus")).toContainText("complete");
  await page.getByRole("button", { name: "T20230715.0124" }).click();

  await expect(page.getByRole("dialog", { name: "Ticket T20230715.0124" })).toBeVisible();
  await expect(page.getByRole("dialog")).toContainText("Outlook offline");
  await expect(page.getByRole("dialog")).toContainText("Status Duration");
  await expect(page.getByRole("dialog")).toContainText("Created as New");
  await expect(page.getByRole("dialog")).toContainText("Initial triage");
});
