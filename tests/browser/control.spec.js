import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function fixture(page, phase = "idle") {
  const state = {
    enabled: true,
    csrf_token: "fixture-token-never-provider-credentials",
    configuration: {
      ready: true,
      destination: "+18054398008",
      caller_id: "+12025550123",
      max_seconds: 240,
    },
    scenarios: [
      { id: "smoke", label: "office information", objective: "Ask about office hours." },
      { id: "reschedule", label: "reschedule", objective: "Change an existing appointment." },
      { id: "refill", label: "refill", objective: "Ask about a refill." },
    ],
    operation: { phase, start_token: "one-confirmation-token-123", live_turns: [] },
  };
  const requests = [];
  let disconnected = false;
  let rejectStart = false;
  await page.route("**/api/console", async (route) => {
    if (disconnected) await route.abort();
    else await route.fulfill({ json: state });
  });
  await page.route("**/api/console/start", async (route) => {
    requests.push({
      route: "start",
      body: route.request().postDataJSON(),
      headers: route.request().headers(),
    });
    state.operation = {
      ...state.operation,
      phase: "connected",
      call_id: "call-browser-fixture",
      live_turns: [
        { idx: 0, role: "patient", text: '<img src=x onerror="alert(1)">Hello', status: "partial" },
      ],
    };
    if (rejectStart) await route.abort();
    else await route.fulfill({ status: 202, json: state.operation });
  });
  await page.route("**/api/console/stop", async (route) => {
    requests.push({ route: "stop", body: route.request().postDataJSON() });
    state.operation = {
      ...state.operation,
      phase: "ended",
      ended_by: "operator_stop",
      stop_requested: true,
      cleanup_confirmed: true,
      evidence_status: "partial_or_unavailable",
    };
    await route.fulfill({ status: 202, json: state.operation });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Run a test call" })).toBeVisible();
  return {
    state,
    requests,
    disconnect: (value) => {
      disconnected = value;
    },
    reject: () => {
      rejectStart = true;
    },
  };
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
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
}

test("confirmed single call, committed dialogue, refresh, stop and saved evidence", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const { requests } = await fixture(page);
  expect(requests).toEqual([]);
  await expect(page.locator("#scenario-objective")).toBeHidden();
  await page.getByText("Scenario details", { exact: true }).click();
  await expect(page.locator("#scenario-objective")).toBeVisible();
  expect(requests).toEqual([]);
  await accessible(page);
  await page.getByRole("button", { name: "Review & call" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("button", { name: "Place one call", exact: true })).toBeDisabled();
  await accessible(page);
  await page.getByRole("checkbox", { name: /I confirm/ }).check();
  await page.getByRole("button", { name: "Place one call", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.locator("#console-phase")).toHaveText("Connected");
  expect(requests).toHaveLength(1);
  expect(requests[0].body.confirmed).toBe(true);
  expect(requests[0].body).not.toHaveProperty("destination");
  expect(requests[0].headers["x-console-token"]).toContain("fixture-token");
  await expect(page.locator("#call-start")).toBeDisabled();
  await page.getByText("Live transcript · committed turns").click();
  await expect(page.locator("#live-turns")).toContainText('<img src=x onerror="alert(1)">Hello');
  await expect(page.locator("#live-turns img")).toHaveCount(0);
  await accessible(page);
  await page.reload();
  await expect(page.locator("#console-phase")).toHaveText("Connected");
  expect(requests).toHaveLength(1);
  await expect(page.locator("#call-start")).toBeDisabled();
  await page.getByRole("button", { name: "Stop call", exact: true }).click();
  await expect(page.locator("#console-phase")).toHaveText("Ended");
  await expect(page.locator("#operation-summary")).toContainText("operator stop");
  await expect(page.locator("#operation-summary")).toContainText("may be incomplete");
  await expect(page.getByRole("link", { name: "Open saved evidence" })).toHaveAttribute(
    "href",
    "?call=call-browser-fixture",
  );
  expect(requests.map((r) => r.route)).toEqual(["start", "stop"]);
  expect(errors).toEqual([]);
});

test("cancel, missing configuration, disconnect and recovery never initiate calls", async ({
  page,
}) => {
  const setup = await fixture(page);
  await page.getByRole("button", { name: "Review & call" }).click();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  expect(setup.requests).toEqual([]);
  setup.state.configuration.ready = false;
  setup.state.configuration.message = "Complete the local configuration.";
  await expect(page.locator("#call-start")).toBeDisabled();
  await expect(page.locator("#console-message")).toContainText("Complete the local configuration");
  setup.state.configuration.ready = true;
  setup.disconnect(true);
  await expect(page.locator("#console-error")).toContainText("Do not assume the call ended");
  await expect(page.locator("#call-start")).toBeDisabled();
  setup.disconnect(false);
  setup.state.operation = {
    ...setup.state.operation,
    phase: "recovery_required",
    call_id: "call-browser-fixture",
    message: "Call termination could not be confirmed.",
  };
  await expect(page.getByRole("button", { name: "Stop / recover" })).toBeVisible();
  await expect(page.locator("#console-error")).toBeHidden();
  await expect(page.locator("#call-start")).toBeDisabled();
  await accessible(page);
  expect(setup.requests).toEqual([]);
});

test("uncertain start response is never automatically retried", async ({ page }) => {
  const setup = await fixture(page);
  setup.reject();
  await page.getByRole("button", { name: "Review & call" }).click();
  await page.getByRole("checkbox", { name: /I confirm/ }).check();
  await page.getByRole("button", { name: "Place one call", exact: true }).click();
  await expect(page.locator("#confirmation-error")).toContainText("No retry was sent");
  await expect(page.getByRole("button", { name: "Place one call", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.locator("#console-phase")).toHaveText("Connected");
  await expect(page.locator("#call-start")).toBeDisabled();
  expect(setup.requests).toHaveLength(1);
});

test("status polling pauses on page exit and resumes without a call on history restore", async ({
  page,
}) => {
  const reads = [];
  page.on("request", (request) => {
    if (request.url().endsWith("/api/console")) reads.push(request);
  });
  await page.clock.install();
  const setup = await fixture(page, "connected");
  const beforeExit = reads.length;
  await page.evaluate(() => dispatchEvent(new PageTransitionEvent("pagehide")));
  await page.clock.runFor(4000);
  expect(reads).toHaveLength(beforeExit);
  expect(setup.requests).toEqual([]);

  setup.state.operation.phase = "finalizing";
  await page.evaluate(() =>
    dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })),
  );
  await expect(page.locator("#console-phase")).toHaveText("Finalizing evidence");
  expect(reads).toHaveLength(beforeExit + 1);
  expect(setup.requests).toEqual([]);

  let held;
  const hold = (route) => {
    held = route;
  };
  await page.route("**/api/console", hold);
  await page.clock.runFor(1000);
  await expect.poll(() => !!held).toBe(true);
  const canceledRead = page.waitForEvent("requestfailed", {
    predicate: (request) => request.url().endsWith("/api/console"),
  });
  await page.evaluate(() => dispatchEvent(new PageTransitionEvent("pagehide")));
  await canceledRead;
  const afterCancel = reads.length;
  await page.clock.runFor(9000);
  expect(reads).toHaveLength(afterCancel);
  await expect(page.locator("#console-error")).toBeHidden();
  expect(setup.requests).toEqual([]);
  await page.unroute("**/api/console", hold);
});

test("scenario picker supports keyboard, dismissal and selection without calling", async ({
  page,
}) => {
  const setup = await fixture(page);
  const picker = page.getByRole("combobox", { name: /Scenario/ });
  await picker.focus();
  await picker.press("ArrowDown");
  await expect(page.getByRole("listbox", { name: "Scenario", exact: true })).toBeVisible();
  await accessible(page);
  await picker.press("End");
  await expect(picker).toHaveAttribute("aria-activedescendant", "scenario-option-2");
  await picker.press("Escape");
  await expect(picker).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator("#scenario")).toHaveValue("smoke");
  await picker.click();
  await picker.press("r");
  await picker.press("Enter");
  await expect(page.locator("#scenario")).toHaveValue("reschedule");
  await expect(picker).toBeFocused();
  await picker.click();
  await page.getByRole("option", { name: "refill", exact: true }).click();
  await expect(page.locator("#scenario")).toHaveValue("refill");
  await picker.click();
  await page.getByRole("heading", { name: "Run a test call" }).click();
  await expect(picker).toHaveAttribute("aria-expanded", "false");
  expect(setup.requests).toEqual([]);
  await page.getByRole("button", { name: "Review & call" }).click();
  await expect(page.locator("#confirmation-description")).toContainText("for refill.");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  setup.state.operation.phase = "connected";
  await expect(picker).toBeDisabled();
  expect(setup.requests).toEqual([]);
});
