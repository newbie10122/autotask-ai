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
  const operationsRequestLog = [];
  await stubApi(page, {
    routeAuthRequired: true,
    user: { username: "admin", roles: ["Admin"] },
    operationsRequestLog
  });

  await page.goto(`${pageUrl}#operations`);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  await expect(page.locator("#opsTimeEntries")).toHaveText("49054");
  await expect(page.locator("#opsTicketHistory")).toHaveText("29340");
  await expect(page.locator("#opsPauseProvenance")).toHaveText("resume by admin");
  await expect(page.locator("#schedulerState")).toHaveText("healthy");
  await expect(page.locator("#schedulerHeartbeat")).toHaveText("12s ago");
  await expect(page.locator("#schedulerNextDue")).toContainText("open_ticket_history_gaps");
  await expect(page.locator("#schedulerAutomationState")).toHaveText("partial_scheduler_automation_evidence");
  await expect(page.locator("#schedulerStaleRuns")).toHaveText("1");
  await expect(page.locator("#schedulerRecoveryStreak")).toHaveText("partial_scheduler_recovery_streak (8/9)");
  await expect(page.locator("#schedulerStaleProvenance")).toContainText("classify_tickets #4143");
  await expect(page.locator("#schedulerStaleProvenance")).toContainText("orphaned_running_row_candidate");
  await expect(page.locator("#schedulerStaleProvenance")).toContainText("Newer Completed");
  await expect(page.locator("#schedulerStaleProvenance")).toContainText("4391");
  await expect(page.locator("#schedulerStaleProvenance button", { hasText: "Archive" })).toBeEnabled();

  const automationPanel = page.locator("#relatedDataAutomation");
  await expect(automationPanel).toContainText("open_ticket_history_gaps");
  await expect(automationPanel).toContainText("ticket_time_entry_gaps");
  await expect(automationPanel).toContainText("Limit");
  await expect(automationPanel).toContainText("100");
  await expect(automationPanel).toContainText("Runs");
  await expect(automationPanel).toContainText("641");
  await expect(automationPanel).toContainText("685");
  await expect(automationPanel).toContainText("40");
  await expect(automationPanel).toContainText("None");

  await expect(page.locator("#fieldCertificationState")).toHaveText("partial_field_certification");
  await expect(page.locator("#fieldCertificationBlockers")).toContainText("status_duration");
  await expect(page.locator("#fieldCertificationParser")).toHaveText("0 status / 0 timestamped");
  const diagnosticPanel = page.locator("#fieldCertificationDiagnostics");
  await expect(diagnosticPanel).toContainText("coverage_backfill");
  await expect(diagnosticPanel).toContainText("source_shape_limited");
  await expect(diagnosticPanel).toContainText("Source limited");
  await expect(diagnosticPanel).toContainText("Continue bounded scheduled TicketHistory gap checks");
  const fieldPanel = page.locator("#fieldCertificationTargets");
  await expect(fieldPanel).toContainText("TicketHistory coverage");
  await expect(fieldPanel).toContainText("source_limited");
  await expect(fieldPanel).toContainText("TimeEntries and labor-hour lineage");
  await expect(fieldPanel).toContainText("Priority current-field/reference lineage");
  await expect(fieldPanel).toContainText("Auth Labels");
  await expect(fieldPanel).toContainText("25%");

  await page.locator("#pauseOperations").click();
  await page.locator("#resumeOperations").click();
  expect(operationsRequestLog).toEqual([
    { pathname: "/api/operations/pause", body: { reason: "manual_ui_pause" } },
    { pathname: "/api/operations/resume", body: { reason: "manual_ui_resume" } }
  ]);
});
