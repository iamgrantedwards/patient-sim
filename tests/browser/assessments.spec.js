import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const pending = { status: "pending", enabled: true, eligible: true, token: "fixture" };
const result = {
  ...pending,
  status: "saved",
  score: { percent: 90, assessed: 5, total: 5 },
  latest: {
    model: "fixture-judge",
    rubric: "transcript-v1",
    created_at: "2026-09-19T22:00:00Z",
    result: {
      summary: "Synthetic assessment. Check the cited response.",
      dimensions: [
        "request_handling",
        "consistency",
        "clarification",
        "supported_claims",
        "next_steps",
      ].map((dimension) => ({
        dimension,
        score: dimension === "consistency" ? 1 : 2,
        rationale: "Fixture explanation.",
        evidence: [{ turn: 0, quote: 'Synthetic fixture: <img src=x onerror="alert(1)">' }],
      })),
      observations: [
        {
          title: "Possible inconsistency",
          expected_behavior: "Consistent response",
          basis_for_expectation: "Earlier turn",
          attribution: "unknown",
          uncertainty: "Listen to verify",
          recommended_improvement: "Clarify the response",
          next_test: "Ask for confirmation",
          evidence: [{ turn: 1, quote: "Synthetic patient fixture." }],
        },
      ],
    },
  },
};

test("assess, inspect evidence and reopen saved result without dialing or human acceptance", async ({
  page,
}) => {
  let saved = false;
  const writes = [];
  await page.route("**/api/calls/call-fixture-03/assessment", async (route) => {
    if (route.request().method() === "POST") {
      saved = true;
      writes.push(route.request().url());
    }
    await route.fulfill({ json: saved ? result : pending });
  });
  await page.goto("/?call=call-fixture-03");
  const panel = page.locator(".assessment-panel");
  await panel.locator(":scope > summary").click();
  await page.getByRole("button", { name: "Assess transcript", exact: true }).click();
  await expect(panel).toContainText("90/100 · provisional");
  await panel.locator(".assessment-dimension summary").first().click();
  await expect(panel.locator("img")).toHaveCount(0);
  await panel.locator(".assessment-citation").first().click();
  await expect(page.locator("#conversation-transcript")).toHaveAttribute("open", "");
  await expect(page.locator('#transcript [data-turn="0"]')).toBeFocused();
  await panel.locator(".assessment-observation summary").click();
  await expect(panel).toContainText("Next test: Ask for confirmation");
  await expect(page.locator(".listening-review > summary")).toContainText("Not reviewed");
  await expect(page.locator(".reviewed-chip")).toHaveCount(0);
  const axe = await new AxeBuilder({ page }).include("#ai-assessment").analyze();
  expect(axe.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await panel.screenshot({ path: test.info().outputPath("assessment-light.png") });
  await page.locator("#theme-toggle").click();
  expect((await new AxeBuilder({ page }).include("#ai-assessment").analyze()).violations).toEqual(
    [],
  );
  await panel.screenshot({ path: test.info().outputPath("assessment-charcoal.png") });
  await page.reload();
  await expect(panel).toContainText("90/100 · provisional");
  await panel.locator(":scope > summary").click();
  await expect(page.getByRole("button", { name: "Assess transcript", exact: true })).toHaveCount(0);
  expect(writes).toHaveLength(1);
});

test("provider failure is retryable and stale results withhold aggregate", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/calls/call-fixture-03/assessment", (route) => {
    if (route.request().method() === "POST") {
      attempts += 1;
      return route.fulfill(
        attempts === 1
          ? { status: 502, json: { error: "Fixture provider failed." } }
          : { json: result },
      );
    }
    return route.fulfill({ json: { ...result, status: "stale", score: null } });
  });
  await page.goto("/?call=call-fixture-03");
  const panel = page.locator(".assessment-panel");
  await panel.locator(":scope > summary").click();
  await expect(panel).toContainText("Evidence changed · reassess");
  await expect(panel).not.toContainText("90/100");
  await page.getByRole("button", { name: "Reassess transcript" }).click();
  await expect(panel).toContainText("Fixture provider failed.");
  await page.getByRole("button", { name: "Retry assessment" }).click();
  await expect(panel).toContainText("90/100");
});

test("late assessment cannot replace a different selected call", async ({ page }) => {
  let release;
  const wait = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/calls/call-fixture-03/assessment", async (route) => {
    if (route.request().method() === "POST") {
      await wait;
      await route.fulfill({ json: result });
    } else await route.fulfill({ json: pending });
  });
  await page.goto("/?call=call-fixture-03");
  await page.locator(".assessment-panel > summary").click();
  await page.getByRole("button", { name: "Assess transcript", exact: true }).click();
  await page.locator('[data-call-id="call-fixture-02"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Rescheduling");
  release();
  await expect(page.locator(".assessment-panel")).not.toContainText("90/100");
});
