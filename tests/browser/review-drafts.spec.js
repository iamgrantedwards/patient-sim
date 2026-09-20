import { expect, test } from "@playwright/test";

const assessment = {
  status: "saved",
  enabled: false,
  eligible: true,
  score: null,
  latest: {
    model: "fixture-judge",
    rubric: "transcript-v1",
    created_at: "2026-09-19T22:00:00Z",
    result: {
      summary: "Possible inconsistency; listen to confirm.",
      dimensions: [],
      observations: [],
    },
  },
};
test.beforeEach(async ({ page }) => {
  await page.route("**/api/reviews", (route) =>
    route.fulfill({ json: { enabled: true, token: "fixture" } }),
  );
});

test("compact review imports fresh AI draft without overwriting notes, grading or saving", async ({
  page,
}) => {
  const writes = [];
  let review;
  page.on("request", (request) => {
    if (request.method() === "POST") writes.push(request.url());
  });
  await page.route("**/api/calls/*/assessment", (route) => route.fulfill({ json: assessment }));
  await page.route("**/api/calls/call-fixture-03/review", (route) => {
    review = route.request().postDataJSON();
    return route.fulfill({ json: { revision: 1 } });
  });
  await page.goto("/?call=call-fixture-03");
  await page.locator(".listening-review > summary").click();
  await expect(page.locator(".review-checklist")).not.toHaveAttribute("open", "");
  await page.getByLabel("Reviewer", { exact: true }).fill("Fixture reviewer");
  const notes = page.getByLabel("Notes and next step");
  await notes.fill("My own observation.");
  await page.getByRole("button", { name: "Add AI summary", exact: true }).click();
  await expect(notes).toHaveValue(
    "My own observation.\n\nAI draft — fixture-judge · transcript-v1\nPossible inconsistency; listen to confirm.",
  );
  expect(writes).toEqual([]);
  await expect(
    page.getByLabel("I listened to the full recording and checked the transcript"),
  ).not.toBeChecked();
  await page.getByRole("button", { name: "Add AI summary", exact: true }).click();
  await expect(page.getByText("This AI summary is already in your notes.")).toBeVisible();
  await page.getByRole("button", { name: "Save review", exact: true }).click();
  await expect.poll(() => review?.reviewer).toBe("Fixture reviewer");
  expect(review.listened).toBe(false);
  expect(review.suitability).toBe("needs_recheck");
  expect(
    Object.values(review.checks).every(
      (check) => check.result === "not_assessed" && check.note === "",
    ),
  ).toBe(true);
  await page.locator('[data-call-id="call-fixture-02"]').click();
  await page.locator(".listening-review > summary").click();
  await expect(page.getByLabel("Reviewer", { exact: true })).toHaveValue("Fixture reviewer");
  await page.locator(".review-checklist > summary").click();
  await expect(page.getByLabel("Ending note", { exact: true })).not.toHaveAttribute("placeholder");
  expect(writes).toHaveLength(1);
});

for (const status of ["stale", "pending"]) {
  test(`${status} AI assessment is not imported`, async ({ page }) => {
    await page.route("**/api/calls/*/assessment", (route) =>
      route.fulfill({ json: { ...assessment, status } }),
    );
    await page.goto("/?call=call-fixture-03");
    await page.locator(".listening-review > summary").click();
    const notes = page.getByLabel("Notes and next step");
    await notes.fill("Keep this.");
    await page.getByRole("button", { name: "Add AI summary", exact: true }).click();
    await expect(notes).toHaveValue("Keep this.");
    await expect(
      page.getByText(
        status === "stale"
          ? "Reassess this call first; the saved AI assessment is out of date."
          : "Run AI assessment for this call first, then add its summary here.",
      ),
    ).toBeVisible();
  });
}
