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
  const wrapper = el("label", null, "review-field");
  input.setAttribute("aria-label", label);
  wrapper.append(el("span", label.endsWith(" note") ? "Observation" : label), input);
  return wrapper;
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
        ? "Save your observations with this call. Original files stay unchanged."
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
  reviewer.value = saved?.reviewer || "";
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
    note.placeholder = "00:42 — what happened?";
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
  fields.append(rows);
  const listened = el("input");
  listened.type = "checkbox";
  listened.checked = state.listened === true;
  listened.disabled = !call.recording.available || !call.transcript_available;
  const listening = el("label", null, "review-listened");
  listening.append(
    listened,
    el("span", "I listened to the full recording and checked the transcript"),
  );
  fields.append(listening);
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
  notes.placeholder = "Outcome, next action, or linked issue";
  notes.value = saved?.summary || "";
  fields.append(field("Notes and next step", notes));
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
      if (!response.ok) throw new Error(result.error || "Review could not be saved.");
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
