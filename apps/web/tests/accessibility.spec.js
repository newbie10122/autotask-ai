const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;
const { startStaticServer, stopStaticServer, stubApi } = require("./helpers");

let server;
let pageUrl;

async function expectFocusedElementHasVisibleIndicator(page) {
  const focusStyle = await page.evaluate(() => {
    const element = document.activeElement;
    const style = window.getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: Number.parseFloat(style.outlineWidth)
    };
  });

  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(focusStyle.outlineWidth).toBeGreaterThan(0);
}

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

test("keyboard focus reaches navigation, auth, and ask workflow controls", async ({ page }) => {
  await stubApi(page, { routeAuthRequired: true, user: { username: "admin", roles: ["Admin", "Technician"] } });
  await page.addInitScript(() => window.localStorage.setItem("autotaskAiToken", "test-token"));
  await page.goto(pageUrl);
  await expect(page.locator("#apiStatus")).toHaveText("API ready");

  const expectedFocusOrder = [
    page.getByRole("link", { name: "Dashboard" }),
    page.getByRole("link", { name: "Ask Assistant" }),
    page.getByRole("link", { name: "Analytics" }),
    page.getByRole("link", { name: "Ticket Health" }),
    page.getByRole("link", { name: "Operations" }),
    page.getByRole("link", { name: "Sync Status" }),
    page.getByRole("link", { name: "Saved Knowledge" }),
    page.getByRole("link", { name: "Audit Log" }),
    page.getByLabel("Username"),
    page.getByLabel("Password"),
    page.getByRole("button", { name: "Sign In" }),
    page.getByRole("button", { name: "Sign Out" }),
    page.getByLabel("Mode"),
    page.locator("#question"),
    page.getByRole("button", { name: "Ask", exact: true })
  ];

  for (const locator of expectedFocusOrder) {
    await page.keyboard.press("Tab");
    await expect(locator).toBeFocused();
    await expectFocusedElementHasVisibleIndicator(page);
  }
});
