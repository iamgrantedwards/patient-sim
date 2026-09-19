import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("review can be completed with keyboard, saved, reopened and amended without dialing", async ({
  page,
}) => {
  // Browser fixture judgments only; API persistence/evidence integrity have separate integration tests.
  let latest = null;
  const history = [];
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() === "POST") mutations.push(request.url());
  });
  await page.route("**/api/reviews", (route) =>
    route.fulfill({ json: { enabled: true, token: "fixture-token" } }),
  );
  await page.route("**/api/calls/call-fixture-03", async (route) => {
    const response = await route.fetch();
    const call = await response.json();
    call.review = {
      ...call.review,
      status: latest ? "saved" : "pending",
      latest,
      history,
      revision: history.length,
      listened: latest?.review.listened || false,
      usable: latest?.review.suitability === "usable",
    };
    await route.fulfill({ json: call });
  });
  await page.route("**/api/calls/call-fixture-03/review", async (route) => {
    latest = {
      review: route.request().postDataJSON(),
      revision: history.length + 1,
      saved_at: "2026-09-19T22:00:00Z",
    };
    history.push(latest);
    await route.fulfill({ json: { revision: latest.revision } });
  });
  await page.goto("/?call=call-fixture-03");
  const panel = page.locator(".listening-review");
  await panel.locator(":scope > summary").focus();
  await page.keyboard.press("Enter");
  await page.getByLabel("Reviewer", { exact: true }).fill("Fixture reviewer");
  await page.getByLabel("Complete evidence", { exact: true }).selectOption("ok");
  await page.getByLabel("Ending", { exact: true }).selectOption("issue");
  await page.getByLabel("Ending note", { exact: true }).fill("00:02 — clipped farewell");
  await page.getByLabel("I listened to the full recording and checked the transcript").check();
  await page.getByLabel("Conversation result").selectOption("usable");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Save review", exact: true }).click();
  await expect(panel.locator(":scope > summary")).toContainText("Reviewed · usable");
  await expect(page.getByRole("button", { name: "Save revision" })).toBeVisible();
  await page.reload();
  await panel.locator(":scope > summary").click();
  await expect(page.getByLabel("Ending note", { exact: true })).toHaveValue(
    "00:02 — clipped farewell",
  );
  await page.getByLabel("Notes and next step").fill("Follow up on ending.");
  await page.getByRole("button", { name: "Save revision" }).click();
  await expect(page.locator(".review-history > summary")).toHaveText("Saved revisions · 2");
  expect(history[0].review.summary).toBe("");
  expect(history[1].review.summary).toBe("Follow up on ending.");
  expect(mutations).toHaveLength(2);
  expect(mutations.every((url) => url.endsWith("/call-fixture-03/review"))).toBe(true);
});

test("read-only review explains enablement and missing evidence cannot confirm listening", async ({
  page,
}) => {
  await page.goto("/?call=call-fixture-01");
  await page.locator(".listening-review > summary").click();
  await expect(
    page.getByText("Read-only. Start with --enable-reviews to save a review."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Save review", exact: true })).toBeDisabled();
  await expect(
    page.getByLabel("I listened to the full recording and checked the transcript"),
  ).toBeDisabled();
});
