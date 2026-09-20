import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function loaded(page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Call recording", exact: true })).toBeVisible();
}

async function accessible(page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    results.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
    })),
  ).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
}

test("original evidence, partial speech, literal unsafe content, and downloadable transcript", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await loaded(page);
  await expect(page.locator("#library-count")).toHaveText("4 calls");
  await expect(page.locator("#metric-pairs")).toHaveText("2");
  await expect(page.locator("#metric-reviewed")).toHaveText("0/4");
  await expect(page.getByText("Listening review pending.", { exact: true })).toBeVisible();
  await page.locator("#conversation-transcript > summary").click();
  await expect(
    page
      .getByRole("tabpanel", { name: "Conversation" })
      .getByText("Incomplete speech", { exact: true }),
  ).toBeVisible();
  await expect(page.locator("#transcript img")).toHaveCount(0);
  await expect(page.locator("#transcript")).toContainText('<img src=x onerror="alert(1)">');
  await expect(page.getByRole("button", { name: /Seek to turn/ })).toHaveCount(0);
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download .txt" }).click();
  expect((await download).suggestedFilename()).toBe("call-fixture-03-transcript.txt");
  await expect(page.getByRole("heading", { name: "Call recording", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
  await accessible(page);
});

test("keyboard tabs expose provenance and concrete controls", async ({ page }) => {
  await loaded(page);
  const conversation = page.getByRole("tab", { name: "Conversation", exact: true });
  await conversation.focus();
  await conversation.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Provenance" })).toBeFocused();
  await expect(page.getByText("fixture-revision-only")).toBeVisible();
  await accessible(page);
  await page.getByRole("tab", { name: "Provenance" }).press("End");
  await expect(page.getByRole("tab", { name: "Controls & data" })).toBeFocused();
  await expect(page.getByText("Read-only · calling disabled", { exact: true })).toBeVisible();
  await expect(page.getByText(/One at a time · fixed test destination/)).toBeVisible();
  await expect(
    page.getByText(/LiveKit, Twilio and inference providers handle live calls/),
  ).toBeVisible();
  await expect(page.getByText("Human oversight", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Not established", { exact: true })).toHaveCount(0);
  await accessible(page);
  await page.getByRole("tab", { name: "Controls & data" }).press("Home");
  await expect(conversation).toBeFocused();
  if (await page.locator("#review-nav").isVisible()) {
    await page.getByRole("button", { name: "Controls & data", exact: true }).click();
    await page.locator("#review-nav").click();
    await expect(conversation).toHaveAttribute("aria-selected", "true");
  }
  await expect(page.getByRole("heading", { name: "Call recording", exact: true })).toBeVisible();
});

test("search, filters, audio loading and genuine offset seeking", async ({ page }) => {
  await loaded(page);
  await page.getByRole("button", { name: /Search and filter calls/ }).click();
  await page.getByLabel("Search calls").fill("reschedule");
  await expect(page.locator(".call-card")).toHaveCount(1);
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: /Rescheduling · call-fixture-02/ }).click();
  await expect(page.getByText("Date not recorded", { exact: true })).toHaveCount(2);
  await expect
    .poll(() => page.locator("audio").evaluate((audio) => audio.readyState))
    .toBeGreaterThan(0);
  expect(await page.locator("audio").evaluate((audio) => audio.paused)).toBe(true);
  await page.locator("#conversation-transcript > summary").click();
  await page.getByRole("button", { name: /Seek to turn/ }).click();
  await expect
    .poll(() => page.locator("audio").evaluate((audio) => audio.currentTime))
    .toBeCloseTo(0.5, 1);
  await page.getByRole("button", { name: /Search and filter calls/ }).click();
  await page.getByLabel("Search calls").fill("");
  await page.getByLabel("Filter calls", { exact: true }).selectOption("partial");
  await expect(page.locator(".call-card")).toHaveCount(1);
  await page.getByLabel("Search calls").fill("no-matching-scenario");
  await expect(page.getByText(/No matching calls/)).toBeVisible();
});

test("missing and malformed evidence remains reviewable without fabricated success", async ({
  page,
}) => {
  await loaded(page);
  await page.getByRole("button", { name: /Search and filter calls/ }).click();
  await page.getByLabel("Filter calls", { exact: true }).selectOption("missing");
  await expect(page.locator(".call-card")).toHaveCount(2);
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: /Missing Recording · call-fixture-01/ }).click();
  await expect(page.locator("audio")).toBeHidden();
  await expect(page.getByText(/Recording unavailable. This call is not an audio/)).toBeVisible();
  await accessible(page);
  await page.getByRole("button", { name: /Unreadable Artifacts/ }).click();
  await expect(page.getByRole("heading", { name: "Call evidence unavailable" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Conversation" })).toBeHidden();
});

test("empty state has project governance without stale call tabs", async ({ page }) => {
  await page.route("**/api/calls", (route) =>
    route.fulfill({ json: { calls: [], truncated: false } }),
  );
  await page.goto("/");
  await expect(page.getByText("No call artifacts yet.", { exact: false })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Your evidence starts here" })).toBeVisible();
  await accessible(page);
  await page.getByRole("button", { name: "Controls & data", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Controls & data" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Conversation" })).toBeDisabled();
  await expect(page.getByRole("tab", { name: "Provenance" })).toBeDisabled();
  if (await page.locator("#review-nav").isVisible()) {
    await page.locator("#review-nav").click();
    await expect(page.getByRole("heading", { name: "Your evidence starts here" })).toBeVisible();
  }
  await accessible(page);
});

test("service failure offers retry and an unreadable audio file exposes an error", async ({
  page,
}) => {
  await page.route("**/api/calls", (route) =>
    route.fulfill({ status: 503, json: { error: "Evidence unavailable." } }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Could not refresh calls");
  await page.unroute("**/api/calls");
  await page.route("**/audio", (route) => route.fulfill({ status: 404 }));
  await page.getByRole("button", { name: "Refresh calls" }).click();
  await expect(page.getByText(/This recording could not be played/)).toBeVisible();
  await expect(page.locator("#global-error")).toBeHidden();
});

test("Cloud evidence is dated, accessible and never accepts a call", async ({ page }) => {
  // Fixture response only; this does not assert a real Cloud session or change raw artifacts.
  await page.route("**/api/calls/call-fixture-03", async (route) => {
    const response = await route.fetch();
    const call = await response.json();
    call.cloud = {
      session_id: "RM_fixture",
      checked_at: 1789846200,
      player_visible: true,
      screenshot_url: "/api/calls/call-fixture-03/cloud-evidence/screenshot",
      note_url: "/api/calls/call-fixture-03/cloud-evidence/note",
    };
    await route.fulfill({ json: call });
  });
  await loaded(page);
  const reviewed = await page.locator("#metric-reviewed").textContent();
  await page.getByRole("tab", { name: "Provenance" }).click();
  const panel = page.getByRole("region", { name: "Cloud evidence" });
  await expect(panel.getByText("Cloud session confirmed")).toBeVisible();
  await expect(panel.getByText("RM_fixture")).toBeVisible();
  await expect(panel.getByText(/Sep 19, 2026/)).toBeVisible();
  await expect(panel.getByText("Pending", { exact: true })).toBeVisible();
  const screenshot = panel.getByRole("link", { name: "View Cloud snapshot" });
  await expect(screenshot).toHaveAttribute(
    "href",
    "/api/calls/call-fixture-03/cloud-evidence/screenshot",
  );
  await screenshot.focus();
  await expect(screenshot).toBeFocused();
  await expect(panel.getByRole("link", { name: "Read verification note" })).toHaveCount(0);
  await expect(page.locator("#metric-reviewed")).toHaveText(reviewed);
  await accessible(page);
  await page.getByRole("button", { name: /Rescheduling · call-fixture-02/ }).click();
  await page.getByRole("tab", { name: "Provenance" }).click();
  await expect(panel.getByText("No Cloud confirmation recorded for this call.")).toBeVisible();
  await expect(panel.getByRole("link")).toHaveCount(0);
  await accessible(page);
});

test("card rail and list preserve selection, URL and stored preference without calls", async ({
  page,
}) => {
  const mutations = [];
  page.on("request", (request) => {
    if (!["GET", "HEAD"].includes(request.method())) mutations.push(request.url());
  });
  await page.route("**/api/calls", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.calls.push(
      ...Array.from({ length: 8 }, (_, i) => ({ ...data.calls[0], call_id: `call-extra-${i}` })),
    );
    await route.fulfill({ json: data });
  });
  await loaded(page);
  await expect(page.getByRole("button", { name: "Card view", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.locator("#search-panel")).toBeHidden();
  const rail = page.locator("#call-list");
  expect(await rail.evaluate((el) => el.scrollWidth > el.clientWidth)).toBe(true);
  const geometry = () =>
    page.locator(".call-card").evaluateAll((cards) =>
      cards.slice(0, 2).map((card) => {
        const { x, y, width, height } = card.getBoundingClientRect();
        return { x, y, width, height };
      }),
    );
  const cardRects = await geometry();
  expect(cardRects[1].x).toBeGreaterThan(cardRects[0].x + cardRects[0].width);
  expect(cardRects[1].y).toBeCloseTo(cardRects[0].y, 0);
  await expect(page.locator("#call-list")).toHaveCSS("display", "flex");
  await page.getByRole("button", { name: /Rescheduling · call-fixture-02/ }).focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/call=call-fixture-02/);
  await expect(page.getByRole("button", { name: /Rescheduling · call-fixture-02/ })).toBeFocused();
  const list = page.getByRole("button", { name: "List view", exact: true });
  await list.click();
  await expect(list).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#call-list")).toHaveCSS("display", "block");
  const listRects = await geometry();
  expect(listRects[1].y).toBeGreaterThanOrEqual(listRects[0].y + listRects[0].height - 1);
  const libraryBox = await page.locator(".call-library").boundingBox();
  const detailBox = await page.locator("#review-panel").boundingBox();
  expect(detailBox.y).toBeGreaterThanOrEqual(libraryBox.y + libraryBox.height - 1);
  expect(listRects[0].width).toBeGreaterThan(libraryBox.width - 60);
  expect(listRects[1].x).toBeCloseTo(listRects[0].x, 0);
  const toolbar = await page
    .locator("#search-toggle, #view-list")
    .evaluateAll((items) => items.map((item) => item.getBoundingClientRect().y));
  expect(Math.abs(toolbar[0] - toolbar[1])).toBeLessThan(8);
  await expect(page.locator('.call-card[aria-current="true"]')).toContainText("call-fixture-02");
  await accessible(page);
  await page.reload();
  await expect(list).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator('.call-card[aria-current="true"]')).toContainText("call-fixture-02");
  await page.getByRole("button", { name: "Card view", exact: true }).click();
  await expect(page.locator("#call-list")).toHaveCSS("display", "flex");
  await page.emulateMedia({ reducedMotion: "reduce" });
  const selected = page.locator('.call-card[aria-current="true"]');
  await selected.hover();
  expect(await selected.evaluate((el) => getComputedStyle(el).transform)).toBe("none");
  expect(await selected.evaluate((el) => getComputedStyle(el).transitionDuration)).toBe("0s");
  await accessible(page);
  expect(mutations).toEqual([]);
});

test("search menu dismisses, shows active filters and clears without losing selection", async ({
  page,
}) => {
  await loaded(page);
  const opener = page.getByRole("button", { name: /Search and filter calls/ });
  await opener.focus();
  await opener.press("Enter");
  const search = page.getByLabel("Search calls", { exact: true });
  await expect(search).toBeFocused();
  await search.fill("reschedule");
  await expect(page.locator("#library-count")).toHaveText("1 of 4");
  await expect(opener).toHaveAccessibleName("Search and filter calls, filters active");
  await accessible(page);
  const box = await page.locator("#search-panel").boundingBox();
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(page.viewportSize().width);
  await search.press("Escape");
  await expect(opener).toBeFocused();
  await expect(page.locator("#search-panel")).toBeHidden();
  await opener.click();
  await expect(search).toHaveValue("reschedule");
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await expect(page.locator("#library-count")).toHaveText("4 calls");
  await expect(search).toBeFocused();
  await expect(opener).toHaveAccessibleName("Search and filter calls");
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(opener).toBeFocused();
  await expect(page.locator('.call-card[aria-current="true"]')).toContainText("call-fixture-03");
  await opener.click();
  await page.locator(".brand-tagline").click();
  await expect(page.locator("#search-panel")).toBeHidden();
});
