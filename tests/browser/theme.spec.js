import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function accessible(page) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
    })),
  ).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
}

test("charcoal preference persists and covers controls, reviews, menus and help without dialing", async ({
  page,
}) => {
  const mutations = [];
  const operation = { phase: "idle", start_token: "fixture-confirmation-token", live_turns: [] };
  page.on("request", (request) => {
    if (!["GET", "HEAD"].includes(request.method())) mutations.push(request.url());
  });
  await page.route("**/api/reviews", (route) =>
    route.fulfill({ json: { enabled: true, token: "fixture-only" } }),
  );
  await page.route("**/api/console", (route) =>
    route.fulfill({
      json: {
        enabled: true,
        csrf_token: "fixture-only",
        configuration: {
          ready: true,
          destination: "+18054398008",
          caller_id: "+12025550123",
          max_seconds: 240,
        },
        scenarios: [
          { id: "smoke", label: "office information", objective: "Ask about office hours." },
        ],
        operation,
      },
    }),
  );
  await page.goto("/");
  await expect(page.locator("#call-content")).toBeVisible();
  await page.getByRole("button", { name: "Use dark mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.getByRole("button", { name: "Use light mode", exact: true })).toBeVisible();
  await expect(page.locator("#call-content")).toBeVisible();
  await page.locator("#conversation-transcript > summary").click();
  await page.locator(".listening-review > summary").click();
  await accessible(page);
  await page.locator(".review-checklist > summary").click();
  await page.getByRole("combobox", { name: "Complete evidence", exact: true }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await page.getByRole("combobox", { name: /Scenario/ }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Search and filter calls", exact: true }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "Provenance", exact: true }).click();
  await accessible(page);
  await page.getByRole("tab", { name: "Controls & data", exact: true }).click();
  await accessible(page);
  await page.getByRole("button", { name: "Open quick guide", exact: true }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Review & call", exact: true }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  operation.phase = "connected";
  operation.call_id = "call-fixture-live";
  operation.live_turns = [
    { idx: 0, role: "patient", text: "What are the office hours?" },
    { idx: 1, role: "remote", text: "We open at nine." },
  ];
  await expect(page.locator("#console-phase")).toHaveText("Connected");
  await expect(page.locator("#live-dialogue")).toHaveJSProperty("open", true);
  await accessible(page);
  await page.getByRole("button", { name: "Use light mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  expect(mutations).toEqual([]);
});

test("theme switches when browser storage is blocked and transcript starts collapsed per call", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => {
      throw new Error("blocked");
    };
    Storage.prototype.setItem = () => {
      throw new Error("blocked");
    };
  });
  await page.goto("/");
  await expect(page.locator("#call-content")).toBeVisible();
  const disclosure = page.locator("#conversation-transcript");
  await expect(disclosure).not.toHaveAttribute("open", "");
  await expect(page.locator("#transcript")).toBeHidden();
  await expect(page.locator("#audio")).toBeVisible();
  await disclosure.locator(":scope > summary").focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#transcript")).toBeVisible();
  await expect(page.getByRole("link", { name: "Download .txt" })).toHaveClass(/button/);
  await page.getByRole("button", { name: "Use dark mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: /Rescheduling · call-fixture-02/ }).click();
  await expect(page.locator("#transcript")).toBeHidden();
  await page.getByRole("button", { name: "Use light mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});
