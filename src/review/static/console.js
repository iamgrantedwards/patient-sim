const byId = (id) => document.getElementById(id);
const terminal = new Set(["idle", "ended", "failed"]);
const phases = {
  idle: "Ready to prepare",
  preparing_worker: "Registering worker",
  dispatching: "Dispatching",
  waiting_for_worker: "Waiting for worker",
  preparing_audio: "Preparing audio",
  dialing: "Dialing",
  connected: "Connected",
  stopping: "Stop requested",
  finalizing: "Finalizing evidence",
  ended: "Ended",
  failed: "Failed",
  recovery_required: "Recovery required",
};
let current;
let pending;
let busy = false;
let lastPhase;
let lastTurns;
let initialized = false;
let statusUnavailable = false;
let pageActive = true;
let pollTimer;
let pollController;

function text(tag, content, className) {
  const element = document.createElement(tag);
  element.textContent = content;
  if (className) element.className = className;
  return element;
}
function error(message) {
  byId("console-error").textContent = message;
  byId("console-error").hidden = !message;
}
// The hidden native select remains the single selected value. This picker only
// changes that value; the existing confirmation flow is the sole call action.
const picker = byId("scenario-picker");
const options = byId("scenario-options");
let activeOption = 0;
let searchKeys = "";
let searchAt = 0;
function highlightOption(index) {
  const items = [...options.children];
  activeOption = Math.max(0, Math.min(index, items.length - 1));
  for (const [i, item] of items.entries()) item.classList.toggle("active", i === activeOption);
  if (items[activeOption]) {
    picker.setAttribute("aria-activedescendant", items[activeOption].id);
    items[activeOption].scrollIntoView({ block: "nearest" });
  }
}
function closeOptions() {
  options.hidden = true;
  picker.setAttribute("aria-expanded", "false");
  picker.removeAttribute("aria-activedescendant");
}
function openOptions() {
  if (picker.disabled) return;
  options.hidden = false;
  picker.setAttribute("aria-expanded", "true");
  highlightOption(byId("scenario").selectedIndex);
}
function selectOption(index) {
  if (picker.disabled) return;
  byId("scenario").selectedIndex = index;
  byId("scenario").dispatchEvent(new Event("change"));
  closeOptions();
  picker.focus();
}
picker.addEventListener("click", () => (options.hidden ? openOptions() : closeOptions()));
picker.addEventListener("keydown", (event) => {
  const count = options.children.length;
  if (!count || picker.disabled) return;
  if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
    event.preventDefault();
    const wasClosed = options.hidden;
    if (wasClosed) openOptions();
    highlightOption(
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? count - 1
          : wasClosed
            ? activeOption
            : (activeOption + (event.key === "ArrowDown" ? 1 : -1) + count) % count,
    );
  } else if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    if (options.hidden) openOptions();
    else selectOption(activeOption);
  } else if (event.key === "Escape" || event.key === "Tab") {
    if (event.key === "Escape") event.preventDefault();
    closeOptions();
  } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    if (Date.now() - searchAt > 700) searchKeys = "";
    searchAt = Date.now();
    searchKeys += event.key.toLowerCase();
    if (options.hidden) openOptions();
    const index = [...options.children].findIndex((item) =>
      item.textContent.toLowerCase().startsWith(searchKeys),
    );
    if (index >= 0) highlightOption(index);
  }
});
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".scenario-field")) closeOptions();
});
picker.addEventListener("blur", () => {
  if (!options.matches(":hover")) closeOptions();
});
function objective() {
  const selected = current?.scenarios.find((item) => item.id === byId("scenario").value);
  byId("scenario-objective").textContent = selected?.objective || "";
  byId("scenario-value").textContent = selected?.label || "Choose a scenario";
  for (const item of options.children)
    item.setAttribute("aria-selected", String(item.dataset.value === selected?.id));
}
function render(data) {
  current = data;
  if (!data.enabled) return;
  byId("console-panel").hidden = false;
  if (!initialized) {
    for (const [index, item] of data.scenarios.entries()) {
      byId("scenario").append(new Option(item.label, item.id));
      const option = text("button", item.label, "scenario-option");
      option.type = "button";
      option.id = `scenario-option-${index}`;
      option.dataset.value = item.id;
      option.setAttribute("role", "option");
      option.tabIndex = -1;
      option.addEventListener("pointerdown", (event) => event.preventDefault());
      option.addEventListener("click", () => selectOption(index));
      options.append(option);
    }
    byId("scope-mark").textContent = "Call controls enabled";
    byId("scope-details").textContent = "One call at a time. Confirmation required.";
    document.dispatchEvent(new CustomEvent("console-mode", { detail: { enabled: true } }));
    initialized = true;
    objective();
  }
  const op = data.operation;
  const active = !terminal.has(op.phase);
  byId("console-phase").textContent = phases[op.phase] || "Unknown state";
  byId("console-phase").className =
    `badge ${["failed", "recovery_required"].includes(op.phase) ? "error" : active ? "warning" : "neutral"}`;
  byId("call-destination").textContent = data.configuration.destination;
  byId("call-caller").textContent = data.configuration.caller_id
    ? `From ${data.configuration.caller_id}`
    : "Caller not configured";
  byId("call-start").disabled = busy || active || !data.configuration.ready;
  byId("scenario").disabled = busy || active;
  picker.disabled = busy || active;
  if (picker.disabled) closeOptions();
  byId("call-stop").hidden = !active || !op.call_id;
  byId("call-stop").disabled = busy || (op.stop_requested && op.phase !== "recovery_required");
  byId("call-stop").textContent = op.phase === "recovery_required" ? "Stop / recover" : "Stop call";
  const message = op.message || data.configuration.message || "";
  byId("console-message").textContent = message;
  byId("console-message").hidden = !message;
  byId("active-operation").hidden = !op.call_id;
  byId("operation-id").textContent = op.call_id || "";
  byId("open-evidence").hidden = !terminal.has(op.phase) || !op.call_id;
  if (op.call_id) byId("open-evidence").href = `?call=${encodeURIComponent(op.call_id)}`;
  const summary = [];
  if (op.stop_requested) summary.push("Operator stop requested.");
  if (op.ended_by) summary.push(`Recorded ending: ${op.ended_by.replaceAll("_", " ")}.`);
  if (op.cleanup_confirmed) summary.push("Call room closed.");
  if (op.evidence_status === "partial_or_unavailable")
    summary.push("Evidence may be incomplete. Review the saved files.");
  byId("operation-summary").textContent = summary.join(" ");
  const turns = JSON.stringify(op.live_turns);
  if (lastTurns !== turns) {
    byId("live-turns").replaceChildren();
    for (const turn of op.live_turns) {
      const entry = text("div", "", `live-turn ${turn.role}`);
      entry.append(
        text("strong", turn.role === "patient" ? "Simulated patient" : "Assessment agent"),
        text("p", turn.text),
      );
      if (turn.status === "partial")
        entry.append(text("span", "Incomplete speech", "badge warning"));
      byId("live-turns").append(entry);
    }
    if (!op.live_turns.length)
      byId("live-turns").append(
        text("p", op.live_warning || "No committed dialogue yet.", "context-note"),
      );
    lastTurns = turns;
  }
  if (lastPhase && lastPhase !== op.phase && terminal.has(op.phase))
    document.dispatchEvent(new CustomEvent("evidence-ready"));
  lastPhase = op.phase;
}
async function poll() {
  if (!pageActive || pollController) return;
  const controller = new AbortController();
  pollController = controller;
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch("/api/console", {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error("status");
    const data = await response.json();
    if (!pageActive || pollController !== controller) return;
    render(data);
    if (statusUnavailable) error("");
    statusUnavailable = false;
  } catch {
    if (pageActive && pollController === controller && initialized) {
      statusUnavailable = true;
      error(
        "Live status is unavailable. Do not assume the call ended. Restore the console connection; provider duration limits still apply.",
      );
      byId("call-start").disabled = true;
    }
  } finally {
    clearTimeout(timeout);
    if (pollController === controller) {
      pollController = undefined;
      if (pageActive && current?.enabled !== false)
        pollTimer = setTimeout(
          poll,
          current && !terminal.has(current.operation.phase) ? 1000 : 3000,
        );
    }
  }
}
// Navigation ends this page's status reads, not the provider call.
window.addEventListener("pagehide", () => {
  pageActive = false;
  clearTimeout(pollTimer);
  const controller = pollController;
  pollController = undefined;
  controller?.abort();
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted && !pageActive) {
    pageActive = true;
    poll();
  }
});
async function mutation(route, body) {
  const response = await fetch(`/api/console/${route}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Console-Token": current.csrf_token },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10000),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || "Request rejected. Refresh status before trying again.");
  return data;
}
byId("scenario").addEventListener("change", objective);
byId("call-start").addEventListener("click", () => {
  const scenario = byId("scenario").value;
  pending = {
    scenario,
    start_token: current.operation.start_token,
    request_id: crypto.randomUUID(),
    confirmed: true,
  };
  byId("confirmation-description").textContent =
    `Call ${current.configuration.destination} from ${current.configuration.caller_id} for ${current.scenarios.find((item) => item.id === scenario).label}. Maximum connected duration: ${current.configuration.max_seconds} seconds.`;
  byId("confirm-ready").checked = false;
  byId("call-confirm").disabled = true;
  byId("confirmation-error").hidden = true;
  byId("call-confirmation").showModal();
});
byId("confirm-ready").addEventListener("change", () => {
  byId("call-confirm").disabled = !byId("confirm-ready").checked || busy;
});
byId("call-cancel").addEventListener("click", () => byId("call-confirmation").close());
byId("call-confirm").addEventListener("click", async () => {
  if (busy || !byId("confirm-ready").checked) return;
  busy = true;
  byId("call-confirm").disabled = true;
  byId("call-cancel").disabled = true;
  try {
    const operation = await mutation("start", pending);
    render({ ...current, operation });
    byId("call-confirmation").close();
    error("");
  } catch (failure) {
    byId("confirmation-error").textContent =
      `${failure.message} No retry was sent. Cancel and check current status before confirming another call.`;
    byId("confirmation-error").hidden = false;
  } finally {
    busy = false;
    byId("call-cancel").disabled = false;
    // Keep this confirmation disabled after an uncertain result; polling reveals the operation.
  }
});
byId("call-stop").addEventListener("click", async () => {
  if (busy || !current.operation.call_id) return;
  busy = true;
  byId("call-stop").disabled = true;
  try {
    const operation = await mutation("stop", { call_id: current.operation.call_id });
    render({ ...current, operation });
    error("");
  } catch (failure) {
    error(`${failure.message} Stop is not confirmed; check status and retry Stop / recover.`);
  } finally {
    busy = false;
  }
});
poll();
