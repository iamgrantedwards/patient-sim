import { expect, test } from "@playwright/test";

test("fast call selection never blanks or fades the current detail panel", async ({ page }) => {
  await page.goto("/?call=call-fixture-03");
  await expect(page.locator("#call-content")).toBeVisible();
  await page.evaluate(() => {
    window.detailFlashes = [];
    const panel = document.getElementById("review-panel");
    const content = document.getElementById("call-content");
    const observer = new MutationObserver(() => {
      if (content.hidden || getComputedStyle(panel).opacity !== "1")
        window.detailFlashes.push("hidden or faded");
    });
    observer.observe(panel, { attributes: true, childList: true, subtree: true });
  });
  await page.locator('[data-call-id="call-fixture-02"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Rescheduling");
  await page.locator('[data-call-id="call-fixture-03"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Office Information");
  expect(await page.evaluate(() => window.detailFlashes)).toEqual([]);
  await expect(page.locator("#call-content")).not.toHaveAttribute("inert", "");
});

test("slow selection retains geometry, blocks stale actions and rejects a superseded response", async ({
  page,
}) => {
  let release;
  const blocked = new Promise((resolve) => {
    release = resolve;
  });
  let finished;
  const settled = new Promise((resolve) => {
    finished = resolve;
  });
  await page.route("**/api/calls/call-fixture-02", async (route) => {
    const response = await route.fetch();
    await blocked;
    try {
      await route.fulfill({ response });
    } finally {
      finished();
    }
  });
  await page.goto("/?call=call-fixture-03");
  await expect(page.locator("#call-content")).toBeVisible();
  const previous = await page.locator("#review-panel").boundingBox();
  await page.locator('[data-call-id="call-fixture-02"]').click();
  await expect(page.locator("#call-content")).toHaveAttribute("inert", "");
  await expect(page.locator("#call-content")).toBeVisible();
  await expect(page.locator("#call-header h2")).toHaveText("Office Information");
  const pending = await page.locator("#review-panel").boundingBox();
  expect(pending.height).toBeCloseTo(previous.height, 0);
  expect(await page.locator("#audio").evaluate((audio) => audio.paused)).toBe(true);
  await expect(page.locator("#call-loading")).toHaveText("Loading Rescheduling…");
  await expect(page.locator("#call-loading")).toBeVisible();
  await page.locator('[data-call-id="call-fixture-01"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Missing Recording");
  release();
  await settled;
  await expect(page.locator("#call-header h2")).toHaveText("Missing Recording");
  await expect(page.locator("#call-loading")).toBeHidden();
  await expect(page.locator("#review-panel")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator("#call-content")).not.toHaveAttribute("inert", "");
});

test("failed replacement clears stale content and a subsequent selection recovers", async ({
  page,
}) => {
  await page.route("**/api/calls/call-fixture-02", (route) =>
    route.fulfill({
      status: 503,
      json: { error: "Fixture read failed." },
    }),
  );
  await page.goto("/?call=call-fixture-03");
  await expect(page.locator("#call-content")).toBeVisible();
  await page.locator('[data-call-id="call-fixture-02"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Call evidence unavailable");
  await expect(page.locator("#call-content")).toBeHidden();
  await expect(page.locator("#call-loading")).toBeHidden();
  await page.locator('[data-call-id="call-fixture-03"]').click();
  await expect(page.locator("#call-header h2")).toHaveText("Office Information");
  await expect(page.locator("#call-content")).toBeVisible();
});
