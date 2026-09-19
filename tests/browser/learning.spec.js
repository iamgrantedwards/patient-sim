import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function load(page) {
  const mutations = [];
  page.on("request", (request) => {
    if (!["GET", "HEAD"].includes(request.method())) mutations.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Call recording", exact: true })).toBeVisible();
  return mutations;
}
async function accessible(page) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    result.violations.map((item) => ({
      id: item.id,
      nodes: item.nodes.map((node) => node.target),
    })),
  ).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
}

test("learning mode defaults off, persists locally, and never mutates calls", async ({ page }) => {
  const mutations = await load(page);
  const toggle = page.getByRole("button", { name: "Learning mode", exact: true });
  const hint = page.getByRole("button", { name: "Help: Call recording", exact: true });
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await expect(hint).toBeHidden();
  await toggle.click();
  await expect(hint).toBeVisible();
  await hint.click();
  await expect(page.getByRole("tooltip")).toContainText("listen all the way through");
  await expect(hint).toHaveAttribute("aria-describedby", "learning-tooltip");
  await accessible(page);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("tooltip")).toBeHidden();
  await expect(hint).toBeFocused();
  await page.reload();
  await expect(toggle).toHaveAttribute("aria-pressed", "true");
  await toggle.click();
  await expect(hint).toBeHidden();
  await page.reload();
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  expect(mutations).toEqual([]);
});

test("keyboard and hover hints keep normal tab actions and stay inside the viewport", async ({
  page,
  isMobile,
}) => {
  await load(page);
  await page.getByRole("button", { name: "Learning mode", exact: true }).click();
  const provenance = page.getByRole("tab", { name: "Provenance", exact: true });
  await provenance.focus();
  await expect(page.getByRole("tooltip")).toContainText("code version saved with this call");
  await page.keyboard.press("Escape");
  await provenance.press("Enter");
  await expect(page.getByText("fixture-revision-only")).toBeVisible();
  await expect(page.getByRole("tooltip")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "Conversation", exact: true }).click();
  await page.keyboard.press("Escape");
  const hint = page.getByRole("button", { name: "Help: Call recording", exact: true });
  if (isMobile) await hint.tap();
  else {
    await hint.hover();
    await page.getByRole("tooltip").hover();
  }
  await expect(page.getByRole("tooltip")).toBeVisible();
  const box = await page.getByRole("tooltip").boundingBox();
  const viewport = page.viewportSize();
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
  expect(box.y).toBeGreaterThanOrEqual(0);
  await accessible(page);
  await page.getByRole("heading", { name: "Call review.", exact: true }).click();
  await expect(page.getByRole("tooltip")).toBeHidden();
});

test("blocked browser storage does not prevent learning or review", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("Blocked", "SecurityError");
      },
    });
  });
  const mutations = await load(page);
  await page.getByRole("button", { name: "Learning mode", exact: true }).click();
  await page.getByRole("button", { name: "Help: Audio + transcript", exact: true }).click();
  await expect(page.getByRole("tooltip")).toContainText("complete, usable conversation");
  await page.getByRole("button", { name: "List view", exact: true }).click();
  await expect(page.getByRole("button", { name: "List view", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(mutations).toEqual([]);
});

test("quick guide works with hints off, traps focus, scrolls and returns to its opener", async ({
  page,
}) => {
  const mutations = await load(page);
  const opener = page.getByRole("button", { name: "Open quick guide", exact: true });
  await opener.click();
  const guide = page.getByRole("dialog", { name: "Quick guide", exact: true });
  await expect(guide).toBeVisible();
  await expect(guide.getByRole("button", { name: "Close quick guide", exact: true })).toBeFocused();
  await expect(page.getByRole("button", { name: "Learning mode", exact: true })).toHaveAttribute(
    "aria-pressed",
    "false",
  );
  await accessible(page);
  await guide.getByText("What do the three tabs mean?", { exact: true }).click();
  await expect(
    guide.getByText("Later changes do not rewrite them.", { exact: false }),
  ).toBeVisible();
  await guide.getByText("How do I stop or recover a call?", { exact: true }).click();
  await expect(
    guide.getByText("Refreshing or closing the browser does not stop a call.", { exact: false }),
  ).toBeVisible();
  await guide.getByText("What are the privacy and AI limits?", { exact: true }).click();
  await expect(
    guide.getByText("The app does not claim HIPAA compliance.", { exact: false }),
  ).toBeVisible();
  await accessible(page);
  const lastTopic = guide.getByText("What are the privacy and AI limits?", { exact: true });
  await lastTopic.focus();
  await page.keyboard.press("Tab");
  await expect(guide.getByRole("button", { name: "Close quick guide", exact: true })).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(lastTopic).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(guide).toBeHidden();
  await expect(opener).toBeFocused();
  await opener.click();
  await guide.getByRole("button", { name: "Close quick guide", exact: true }).click();
  await expect(guide).toBeHidden();
  await expect(opener).toBeFocused();
  expect(mutations).toEqual([]);
});
