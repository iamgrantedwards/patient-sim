let reviewerName = "";
function rememberedReviewer() {
  try {
    return sessionStorage.getItem("patient-sim-reviewer") || reviewerName;
  } catch {
    return reviewerName;
  }
}
function rememberReviewer(name) {
  reviewerName = name;
  try {
    sessionStorage.setItem("patient-sim-reviewer", name);
  } catch {
    // A blocked browser store should not prevent a review from being saved.
  }
}
const criteria = [
  ["completeness", "Complete evidence"],
  ["transcript", "Transcript accuracy"],
  ["patient", "Patient behavior"],
  ["turn_taking", "Turn-taking"],
  ["pacing", "Pacing"],
  ["audio", "Audio clarity"],
  ["ending", "Ending"],
];
const el = (tag, text, className) => {
  const item = document.createElement(tag);
  if (text) item.textContent = text;
  if (className) item.className = className;
  return item;
};
function field(label, input) {
  const wrapper = el(input.tagName === "SELECT" ? "div" : "label", null, "review-field");
  input.setAttribute("aria-label", label);
  wrapper.append(
    el("span", label.endsWith(" note") ? "Observation" : label),
    input.tagName === "SELECT" ? picker(input, label) : input,
  );
  return wrapper;
}
let closeActivePicker = () => {};
let pickerSequence = 0;
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".review-picker-field")) closeActivePicker();
});
function picker(input, label) {
  const container = el("div", null, "review-picker-field");
  input.hidden = true;
  const trigger = el("button", null, "review-picker");
  trigger.type = "button";
  trigger.setAttribute("role", "combobox");
  trigger.setAttribute("aria-label", label);
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");
  const value = el("span");
  const chevron = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  for (const [key, value] of Object.entries({
    "aria-hidden": "true",
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2",
  }))
    chevron.setAttribute(key, value);
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "m6 9 6 6 6-6");
  chevron.append(path);
  trigger.append(value, chevron);
  const menu = el("div", null, "review-options");
  menu.id = `review-options-${++pickerSequence}`;
  menu.setAttribute("role", "listbox");
  menu.setAttribute("aria-label", label);
  menu.hidden = true;
  trigger.setAttribute("aria-controls", menu.id);
  const items = [...input.options].map((option, index) => {
    const button = el("button", option.textContent, "scenario-option");
    button.type = "button";
    button.tabIndex = -1;
    button.id = `${menu.id}-${index}`;
    button.setAttribute("role", "option");
    button.addEventListener("pointerdown", (event) => event.preventDefault());
    button.addEventListener("click", () => choose(index));
    menu.append(button);
    return button;
  });
  let active = input.selectedIndex;
  let keys = "";
  let keyTime = 0;
  function sync() {
    value.textContent = input.options[input.selectedIndex].textContent;
    items.forEach((item, index) => {
      item.setAttribute("aria-selected", String(index === input.selectedIndex));
    });
  }
  function highlight(index) {
    active = index;
    items.forEach((item, i) => {
      item.classList.toggle("active", i === active);
    });
    trigger.setAttribute("aria-activedescendant", items[active].id);
    items[active].scrollIntoView({ block: "nearest" });
  }
  function close() {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    trigger.removeAttribute("aria-activedescendant");
  }
  function open() {
    closeActivePicker();
    closeActivePicker = close;
    menu.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    highlight(input.selectedIndex);
  }
  function choose(index) {
    input.selectedIndex = index;
    input.dispatchEvent(new Event("change"));
    sync();
    close();
    trigger.focus();
  }
  trigger.addEventListener("click", () => (menu.hidden ? open() : close()));
  trigger.addEventListener("blur", close);
  trigger.addEventListener("keydown", (event) => {
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const closed = menu.hidden;
      if (closed) open();
      highlight(
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? items.length - 1
            : closed
              ? active
              : (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length,
      );
    } else if (["Enter", " "].includes(event.key)) {
      event.preventDefault();
      if (menu.hidden) open();
      else choose(active);
    } else if (["Escape", "Tab"].includes(event.key)) {
      if (event.key === "Escape") event.preventDefault();
      close();
    } else if (event.key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
      if (Date.now() - keyTime > 700) keys = "";
      keyTime = Date.now();
      keys += event.key.toLowerCase();
      if (menu.hidden) open();
      const found = items.findIndex((item) => item.textContent.toLowerCase().startsWith(keys));
      if (found >= 0) highlight(found);
    }
  });
  sync();
  container.append(input, trigger, menu);
  return container;
}
function select(options, value) {
  const input = el("select");
  for (const [key, label] of options) {
    const option = el("option", label);
    option.value = key;
    input.append(option);
  }
  input.value = value;
  return input;
}
export async function renderReview(call, onSaved) {
  const target = document.getElementById("listening-review");
  target.replaceChildren();
  const state = call.review || { status: "pending" };
  const saved = state.latest?.review;
  const panel = el("details", null, "listening-review");
  const summary = el("summary");
  const status =
    state.status === "stale"
      ? "Evidence changed · recheck"
      : state.status === "unavailable"
        ? "Review unavailable"
        : state.listened
          ? state.usable
            ? "Reviewed · usable"
            : "Listening complete"
          : saved
            ? "Draft saved"
            : "Not reviewed";
  summary.append(el("span", "Review", "review-title"), el("span", status, "review-status"));
  panel.append(summary);
  target.append(panel);
  const message = el("p", "Loading review…", "context-note");
  panel.append(message);
  let configuration;
  try {
    const response = await fetch("/api/reviews", { cache: "no-store" });
    if (!response.ok) throw new Error();
    configuration = await response.json();
  } catch {
    message.textContent = "Review controls unavailable. Refresh to retry.";
    return;
  }
  if (!target.contains(panel)) return;
  message.textContent =
    state.status === "stale"
      ? "The saved review belongs to earlier evidence. Listen again before confirming."
      : configuration.enabled
        ? "Save an outcome or a short note. The detailed checklist is optional."
        : "Read-only. Start with --enable-reviews to save a review.";
  const form = el("form", null, "review-form");
  const fields = el("fieldset");
  fields.disabled = !configuration.enabled || state.status === "unavailable";
  fields.append(el("legend", "Listening checklist", "sr-only"));
  const reviewer = el("input");
  reviewer.type = "text";
  reviewer.required = true;
  reviewer.maxLength = 100;
  reviewer.autocomplete = "name";
  reviewer.value = saved?.reviewer || rememberedReviewer();
  fields.append(field("Reviewer", reviewer));
  const checks = {};
  const rows = el("div", null, "review-checks");
  for (const [key, label] of criteria) {
    const row = el("div", null, "review-check");
    const result = select(
      [
        ["not_assessed", "Not assessed"],
        ["ok", "OK"],
        ["issue", "Issue"],
      ],
      saved?.checks[key]?.result || "not_assessed",
    );
    const note = el("input");
    note.type = "text";
    note.maxLength = 1200;
    note.value = saved?.checks[key]?.note || "";
    const update = () => {
      note.required = result.value === "issue";
    };
    result.addEventListener("change", update);
    update();
    row.append(field(label, result), field(`${label} note`, note));
    rows.append(row);
    checks[key] = { result, note };
  }
  const checklist = el("details", null, "review-checklist");
  checklist.open = Object.values(saved?.checks || {}).some(
    (check) => check.result !== "not_assessed" || check.note,
  );
  checklist.append(
    el("summary", "Detailed checklist (optional)"),
    el("p", "Assess only what you checked. Leave the rest as Not assessed.", "context-note"),
    rows,
  );
  const listened = el("input");
  listened.type = "checkbox";
  listened.checked = state.listened === true;
  listened.disabled = !call.recording.available || !call.transcript_available;
  const listening = el("label", null, "review-listened");
  listening.append(
    listened,
    el("span", "I listened to the full recording and checked the transcript"),
  );

  if (listened.disabled)
    fields.append(
      el("p", "Audio and transcript are required to confirm listening.", "context-note"),
    );
  const suitability = select(
    [
      ["needs_recheck", "Needs recheck"],
      ["usable", "Usable conversation"],
      ["incomplete", "Incomplete attempt"],
    ],
    state.status === "stale" ? "needs_recheck" : saved?.suitability || "needs_recheck",
  );
  fields.append(field("Conversation result", suitability));
  const notes = el("textarea");
  notes.rows = 2;
  notes.maxLength = 2000;
  notes.value = saved?.summary || "";
  const notesField = field("Notes and next step", notes);
  notesField.firstChild.textContent = "Notes (optional)";
  fields.append(notesField);
  const aiDraft = el("button", "Add AI summary", "button");
  aiDraft.type = "button";
  const draftFeedback = el("p", null, "context-note");
  draftFeedback.setAttribute("role", "status");
  fields.append(aiDraft, draftFeedback, checklist, listening);
  aiDraft.addEventListener("click", async () => {
    aiDraft.disabled = true;
    draftFeedback.textContent = "Reading saved assessment…";
    try {
      const response = await fetch(`/api/calls/${encodeURIComponent(call.call_id)}/assessment`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Saved assessment could not load. Try again.");
      const assessment = await response.json();
      if (!target.contains(panel)) return;
      if (assessment.status !== "saved" || !assessment.latest) {
        draftFeedback.textContent =
          assessment.status === "stale"
            ? "Reassess this call first; the saved AI assessment is out of date."
            : "Run AI assessment for this call first, then add its summary here.";
        return;
      }
      const draft = `AI draft — ${assessment.latest.model} · ${assessment.latest.rubric}\n${assessment.latest.result.summary}`;
      if (notes.value.includes(draft)) {
        draftFeedback.textContent = "This AI summary is already in your notes.";
        return;
      }
      const combined = notes.value ? `${notes.value}\n\n${draft}` : draft;
      if (combined.length > notes.maxLength) {
        draftFeedback.textContent =
          "Not enough space for the full summary. Shorten the notes or keep the assessment separate.";
        return;
      }
      notes.value = combined;
      draftFeedback.textContent = "Added as draft notes. Check or edit them before saving.";
    } catch (error) {
      if (target.contains(panel))
        draftFeedback.textContent = error.message || "Could not load the AI summary.";
    } finally {
      aiDraft.disabled = false;
    }
  });
  form.addEventListener(
    "invalid",
    (event) => {
      if (checklist.contains(event.target)) checklist.open = true;
    },
    true,
  );
  const save = el("button", saved ? "Save revision" : "Save review", "button primary");
  save.type = "submit";
  fields.append(save);
  const feedback = el("p", null, "review-feedback");
  feedback.setAttribute("role", "status");
  form.append(fields, feedback);
  panel.append(form);
  if (state.history?.length) {
    const history = el("details", null, "review-history");
    history.append(el("summary", `Saved revisions · ${state.history.length}`));
    for (const entry of [...state.history].reverse()) {
      const item = el("details");
      item.append(
        el(
          "summary",
          `Revision ${entry.revision} · ${entry.review.reviewer} · ${new Date(entry.saved_at).toLocaleString()}`,
        ),
      );
      item.append(
        el(
          "p",
          `${entry.review.listened ? "Listening confirmed" : "Listening pending"} · ${entry.review.suitability.replaceAll("_", " ")}`,
        ),
      );
      for (const [key, label] of criteria)
        item.append(
          el(
            "p",
            `${label}: ${entry.review.checks[key].result.replaceAll("_", " ")}${entry.review.checks[key].note ? ` — ${entry.review.checks[key].note}` : ""}`,
          ),
        );
      item.append(el("p", entry.review.summary));
      history.append(item);
    }
    panel.append(history);
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    save.disabled = true;
    feedback.textContent = "Saving…";
    const payload = {
      reviewer: reviewer.value.trim(),
      listened: listened.checked,
      suitability: suitability.value,
      summary: notes.value,
      checks: Object.fromEntries(
        Object.entries(checks).map(([key, inputs]) => [
          key,
          { result: inputs.result.value, note: inputs.note.value },
        ]),
      ),
      base_revision: state.revision,
      fingerprints: state.fingerprints,
    };
    try {
      const response = await fetch(`/api/calls/${encodeURIComponent(call.call_id)}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Review-Token": configuration.token },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 422) checklist.open = true;
        throw new Error(result.error || "Review could not be saved.");
      }
      rememberReviewer(payload.reviewer);
      feedback.textContent = `Saved revision ${result.revision}.`;
      fields.disabled = true;
      await onSaved(call.call_id);
    } catch (error) {
      feedback.textContent =
        error.message || "Could not save. Refresh to check whether it reached the server.";
      save.disabled = false;
    }
  });
}
