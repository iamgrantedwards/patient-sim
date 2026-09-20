import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("call cards distinguish AI scores, missing coverage, stale results and human review", async ({
  page,
}) => {
  let assessment = { status: "pending", score: null };
  let review = { status: "pending", listened: false, usable: false };
  const writes = [];
  page.on("request", (r) => {
    if (r.method() === "POST") writes.push(r.url());
  });
  await page.route("**/api/calls", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    Object.assign(
      data.calls.find((c) => c.call_id === "call-fixture-03"),
      { assessment, review },
    );
    await route.fulfill({ json: data });
  });
  await page.goto("/?call=call-fixture-03");
  const card = page.locator('[data-call-id="call-fixture-03"]');
  const cases = [
    ["pending", null, "pending", false, "AI unassessed", "Not reviewed"],
    ["saved", { percent: 90, assessed: 5, total: 5 }, "saved", false, "AI 90/100", "Notes saved"],
    [
      "saved",
      { percent: null, assessed: 2, total: 5 },
      "saved",
      true,
      "AI assessed · N/A",
      "Human reviewed",
    ],
    ["stale", null, "stale", false, "AI outdated", "Review outdated"],
    ["unavailable", null, "unavailable", false, "AI unavailable", "Review unavailable"],
    ["saved", { percent: 0, assessed: 5, total: 5 }, "saved", true, "AI 0/100", "Human reviewed"],
  ];
  for (const [status, score, humanStatus, listened, aiLabel, humanLabel] of cases) {
    assessment = { status, score };
    review = { status: humanStatus, listened, usable: false };
    await page.locator("#refresh").click();
    await expect(card.locator(".ai-evaluation")).toHaveText(aiLabel);
    await expect(card.locator(".human-evaluation")).toHaveText(humanLabel);
    await expect(card).toHaveAccessibleName(
      new RegExp(aiLabel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    );
    await expect(card.locator(".reviewed-chip")).toHaveCount(0);
  }
  assessment = {
    status: "stale",
    score: null,
    previous_score: { percent: 90, assessed: 5, total: 5 },
  };
  await page.locator("#refresh").click();
  await expect(card.locator(".ai-evaluation")).toHaveText("AI 90/100 · prior");
  await expect(card.locator(".ai-evaluation")).toHaveAttribute(
    "title",
    /Previous provisional score/,
  );
  for (const mode of ["cards", "list"]) {
    await page.locator(`#view-${mode}`).click();
    for (const theme of ["light", "dark"]) {
      if (theme === "dark") await page.locator("#theme-toggle").click();
      expect((await new AxeBuilder({ page }).include("#call-list").analyze()).violations).toEqual(
        [],
      );
      expect(await card.evaluate((el) => el.scrollWidth <= el.clientWidth)).toBe(true);
      await card.screenshot({ path: test.info().outputPath(`card-${mode}-${theme}.png`) });
    }
    await page.locator("#theme-toggle").click();
  }
  expect(writes).toEqual([]);
});
