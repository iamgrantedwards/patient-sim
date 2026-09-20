import { renderReview } from "./reviews.js";

const $ = (id) => document.getElementById(id);
const state = {
  calls: [],
  selected: null,
  detail: null,
  controller: null,
  controls: false,
  view: "cards",
  operation: null,
};

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = String(text);
  if (className) element.className = className;
  return element;
}
function icon(paths, size = 14) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  for (const [key, value] of Object.entries({
    "aria-hidden": "true",
    class: "status-icon",
    viewBox: "0 0 24 24",
    width: String(size),
    height: String(size),
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.7",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  }))
    svg.setAttribute(key, value);
  for (const data of paths) {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", data);
    svg.append(path);
  }
  return svg;
}
function badge(text, variant = "neutral") {
  return node("span", text, `badge ${variant}`);
}
function duration(value) {
  if (!Number.isFinite(value)) return "—";
  const seconds = Math.floor(value);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}
function date(value, compact = false) {
  if (!Number.isFinite(value) || !Number.isFinite(new Date(value * 1000).getTime()))
    return "Date not recorded";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    ...(compact ? {} : { year: "numeric" }),
    hour: "numeric",
    minute: "2-digit",
    ...(compact ? {} : { timeZoneName: "short" }),
  }).format(new Date(value * 1000));
}
const scenarioPresentation = {
  smoke: ["Office Information", "Hours, location and visit prep."],
  calibration: ["Office Information", "Hours, location and visit prep."],
  schedule: ["Appointment Scheduling", "Book and confirm a visit."],
  reschedule: ["Rescheduling", "Change an appointment time."],
  cancel: ["Cancellation", "Cancel a scheduled visit."],
  refill: ["Medication Refill", "Request a medication refill."],
  "refill-details": ["Refill Missing Information", "Ask with missing refill details."],
  insurance: ["Insurance Questions", "Clarify insurance requirements."],
  correction: ["Availability Correction", "Revise a time preference."],
  ambiguity: ["Unclear Request", "Clarify a vague visit request."],
  proxy: ["Third Party Request", "Ask about helping a relative."],
};
function scenario(value) {
  return (
    scenarioPresentation[value]?.[0] ||
    value?.replace(/[-_]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) ||
    "Unknown Scenario"
  );
}
function outcome(call) {
  const values = {
    remote_hangup: ["Remote hangup", "warning"],
    end_call_tool: ["Caller ended", "neutral"],
    failsafe: ["Failsafe ended", "warning"],
    worker_error: ["Worker error", "error"],
    sip_error: ["Connection error", "error"],
    dispatch_error: ["Dispatch error", "error"],
    no_answer: ["No answer", "warning"],
    rejected: ["Call declined", "warning"],
  };
  if (call.status === "unavailable") return ["Artifacts unavailable", "error"];
  if (call.status === "worker_started" && call.ended_by === "Not recorded")
    return ["Not finalized", "warning"];
  return (
    values[call.ended_by] || [
      call.ended_by === "Not recorded"
        ? call.status.replaceAll("_", " ")
        : call.ended_by.replaceAll("_", " "),
      "neutral",
    ]
  );
}
function link(text, href) {
  const element = node("a", text, "text-link");
  element.href = href;
  element.target = "_blank";
  element.rel = "noreferrer";
  return element;
}
async function json(url, signal) {
  const response = await fetch(url, { signal, cache: "no-store", credentials: "same-origin" });
  if (!response.ok) {
    let message = "The local review service is unavailable. Refresh to retry.";
    try {
      message = (await response.json()).error || message;
    } catch {
      /* Generic response for non-JSON errors. */
    }
    throw new Error(message);
  }
  return response.json();
}
const viewPreference = "patient-sim.call-view.v1";
try {
  if (localStorage.getItem(viewPreference) === "list") state.view = "list";
} catch {
  // The view toggle also works without browser storage.
}
function railControls() {
  const rail = $("call-list");
  const overflow = state.view === "cards" && rail.scrollWidth > rail.clientWidth + 2;
  $("rail-controls").hidden = !overflow;
  $("rail-prev").disabled = rail.scrollLeft < 2;
  $("rail-next").disabled = rail.scrollLeft >= rail.scrollWidth - rail.clientWidth - 2;
}
function setView(view) {
  state.view = view;
  $("calls").dataset.view = view;
  for (const name of ["cards", "list"])
    $(`view-${name}`).setAttribute("aria-pressed", String(name === view));
  try {
    localStorage.setItem(viewPreference, view);
  } catch {
    /* Page-local fallback. */
  }
  requestAnimationFrame(railControls);
}
let operationReceipt = "";
function renderOperation() {
  const op = state.operation;
  const receipt = JSON.stringify([
    op?.call_id,
    op?.phase,
    op?.ended_by,
    op?.cleanup_confirmed,
    op?.evidence_status,
  ]);
  if (operationReceipt === receipt) return;
  operationReceipt = receipt;
  const target = $("latest-operation");
  target.replaceChildren();
  target.hidden = !op?.call_id || !["ended", "failed"].includes(op.phase);
  if (target.hidden) return;
  const open = node("button", "Latest attempt", "footer-link");
  open.type = "button";
  open.addEventListener("click", () => selectCall(op.call_id));
  const status =
    op.ended_by === "operator_stop"
      ? "Stopped by operator"
      : op.phase === "failed"
        ? "Failed"
        : "Ended";
  target.append(open, node("span", status));
  if (op.cleanup_confirmed === true) target.append(node("span", "Room closed"));
  if (op.evidence_status === "partial_or_unavailable")
    target.append(node("span", "Evidence incomplete"));
}
function closeSearch(focus = false) {
  $("search-panel").hidden = true;
  $("search-toggle").setAttribute("aria-expanded", "false");
  if (focus) $("search-toggle").focus();
}
function renderList() {
  const focusedCall = document.activeElement?.closest(".call-card")?.dataset.callId;
  const scrollLeft = $("call-list").scrollLeft;
  const query = $("search").value.trim().toLowerCase();
  const filter = $("filter").value;
  const calls = state.calls.filter((call) => {
    const matches = `${scenario(call.scenario)} ${call.scenario} ${call.call_id} ${call.ended_by}`
      .toLowerCase()
      .includes(query);
    return (
      matches &&
      (filter === "all" ||
        (filter === "usable" && call.review?.usable === true) ||
        (filter === "pending" && call.review?.listened !== true) ||
        (filter === "partial" && call.partial_turns > 0) ||
        (filter === "missing" && (!call.recording.available || !call.transcript_available)))
    );
  });
  const filtered = !!query || filter !== "all";
  $("search-toggle").classList.toggle("has-filter", filtered);
  $("search-toggle").setAttribute(
    "aria-label",
    filtered ? "Search and filter calls, filters active" : "Search and filter calls",
  );
  $("library-count").textContent = filtered
    ? `${calls.length} of ${state.calls.length}`
    : `${calls.length} ${calls.length === 1 ? "call" : "calls"}`;
  $("call-list").replaceChildren();
  if (!calls.length) {
    $("call-list").append(
      node(
        "p",
        state.calls.length
          ? "No matching calls. Try another search or filter."
          : "No call artifacts yet. Refresh after a call has been saved.",
        "empty-small",
      ),
    );
    requestAnimationFrame(railControls);
    return;
  }
  for (const call of calls) {
    const button = node("button", null, "call-card");
    button.type = "button";
    button.dataset.callId = call.call_id;
    button.setAttribute("aria-controls", "review-panel");
    button.setAttribute("aria-current", String(state.selected === call.call_id));
    button.setAttribute(
      "aria-label",
      `${scenario(call.scenario)} · ${call.call_id} · ${outcome(call)[0]} · ${call.recording.available ? "Audio available" : "No audio"} · ${call.transcript_available ? "Transcript available" : "No transcript"} · ${Number.isFinite(call.duration_seconds) ? `Duration ${duration(call.duration_seconds)}` : "Duration unavailable"}`,
    );
    const top = node("div", null, "card-top");
    const time = node("span", null, "duration");
    time.title = Number.isFinite(call.duration_seconds)
      ? "Recording duration"
      : "Recording duration unavailable";
    time.append(
      icon(["M21 12a9 9 0 1 1-18 0a9 9 0 0 1 18 0", "M12 7v5l3 2"]),
      node("span", duration(call.duration_seconds)),
    );
    top.append(node("h3", scenario(call.scenario)));
    const description = node(
      "p",
      scenarioPresentation[call.scenario]?.[1] || "Review the conversation outcome.",
      "card-description",
    );
    description.title = description.textContent;
    top.append(description);
    const status = node("div", null, "card-status");
    status.append(time, badge(...outcome(call)));
    const emblem = node("div", null, "card-emblem");
    const symbol = node("span", null, "card-symbol");
    symbol.append(
      icon(
        [
          "M21 16v3a2 2 0 0 1-2.2 2A19 19 0 0 1 3 5.2 2 2 0 0 1 5 3h3l2 5-3 2a14 14 0 0 0 7 7l2-3 5 2Z",
        ],
        16,
      ),
    );
    emblem.append(symbol, node("span", date(call.started_at, true), "card-date"));
    if (call.review?.usable === true) {
      emblem.append(node("span", "Usable", "reviewed-chip"));
      button.setAttribute(
        "aria-label",
        `${button.getAttribute("aria-label")} · Reviewed usable conversation`,
      );
    }
    const files = node("div", null, "card-files");
    for (const [available, label, paths] of [
      [
        call.recording.available,
        "Audio",
        ["M4 13v-1a8 8 0 0 1 16 0v1", "M4 12H3v7h4v-7H4ZM20 12h1v7h-4v-7h3Z"],
      ],
      [call.transcript_available, "Transcript", ["M14 3H5v18h14V8l-5-5ZM14 3v5h5M8 12h8M8 16h6"]],
    ]) {
      const file = node("span", null, `file-chip ${available ? "file-present" : "file-missing"}`);
      file.title = `${label} file ${available ? "available" : "unavailable"}`;
      file.append(icon(paths), node("span", available ? label : `No ${label.toLowerCase()}`));
      files.append(file);
    }
    button.append(emblem, top, node("p", call.call_id, "call-id mono"), status, files);
    button.addEventListener("click", () => selectCall(call.call_id));
    $("call-list").append(button);
    if (focusedCall === call.call_id) button.focus({ preventScroll: true });
  }
  $("call-list").scrollLeft = scrollLeft;
  requestAnimationFrame(railControls);
}
function selectTab(name, focus = false) {
  for (const tab of document.querySelectorAll('[role="tab"]')) {
    const selected = tab.id === `tab-${name}`;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    $(tab.getAttribute("aria-controls")).hidden = !selected;
    tab.disabled = !state.detail && tab.id !== "tab-governance";
    if (selected && focus) tab.focus();
  }
}
function emptyHeader(title, text) {
  const box = node("div", null, "empty-state");
  box.append(node("span", "◫", "empty-symbol"), node("h2", title), node("p", text));
  $("call-header").replaceChildren(box);
}
function renderHeader(call) {
  const top = node("div", null, "detail-top");
  const title = node("div");
  title.append(node("div", "CALL DETAILS", "detail-kicker"), node("h2", scenario(call.scenario)));
  top.append(title, badge(...outcome(call)));
  const meta = node("div", null, "detail-meta");
  meta.append(
    node("span", date(call.started_at)),
    node("span", "·"),
    node("span", `${call.turn_count} turns`),
    node("span", "·"),
    node("span", call.call_id, "mono"),
  );
  $("call-header").replaceChildren(top, meta);
}
function renderConversation(call) {
  const audio = $("audio");
  audio.pause();
  audio.removeAttribute("src");
  $("audio-error").hidden = true;
  audio.hidden = !call.recording.available;
  if (call.recording.available) audio.src = call.recording.url;
  audio.load();
  $("recording-label").textContent = call.recording.available
    ? `${call.recording.format} · ${duration(call.duration_seconds)}`
    : "UNAVAILABLE";
  $("audio-caption").textContent = call.recording.available
    ? "Original recording"
    : "No original audio file is available.";
  const notices = $("call-notices");
  notices.replaceChildren();
  if (call.review?.listened !== true) {
    const notice = node("div", null, "notice");
    notice.append(
      node("strong", "Listening review pending. "),
      node("span", "Listen to the full call and check the transcript."),
    );
    notices.append(notice);
  }
  for (const warning of call.warnings)
    notices.append(
      node(
        "div",
        warning === "Incomplete speech is present. Listen before drawing a conclusion."
          ? "Incomplete speech. Check the recording."
          : warning,
        "notice",
      ),
    );
  const transcript = $("transcript");
  transcript.replaceChildren();
  const timingCount = call.turns.filter((turn) => Number.isFinite(turn.audio_start_ms)).length;
  $("timing-note").textContent = timingCount
    ? `${timingCount}/${call.turn_count} turns timed. Select a timestamp to seek.`
    : "Audio timestamps not measured.";
  $("download-transcript").hidden = !call.transcript_available;
  $("download-transcript").href = `/api/calls/${encodeURIComponent(call.call_id)}/transcript`;
  $("download-transcript").download = `${call.call_id}-transcript.txt`;
  if (!call.turns.length)
    transcript.append(
      node("p", "No committed dialogue is available for this call.", "empty-small"),
    );
  for (const turn of call.turns) {
    const section = node(
      "div",
      null,
      `turn ${turn.role} ${turn.status === "partial" || turn.interrupted ? "partial" : ""}`,
    );
    const icon = node("span", turn.role === "patient" ? "P" : "A", "speaker-icon");
    icon.setAttribute("aria-hidden", "true");
    const body = node("div");
    const head = node("div", null, "turn-head");
    head.append(
      node(
        "span",
        turn.role === "patient" ? "Simulated patient" : "Assessment agent",
        "speaker-name",
      ),
    );
    if (turn.status === "partial" || turn.interrupted)
      head.append(badge("Incomplete speech", "warning"));
    if (Number.isFinite(turn.audio_start_ms) && call.recording.available) {
      const seek = node("button", duration(turn.audio_start_ms / 1000), "turn-seek");
      seek.type = "button";
      seek.setAttribute("aria-label", `Seek to turn ${turn.idx + 1}`);
      seek.addEventListener("click", () => {
        audio.currentTime = turn.audio_start_ms / 1000;
      });
      head.append(seek);
    }
    head.append(node("span", `TURN ${String(turn.idx + 1).padStart(2, "0")}`, "turn-order"));
    body.append(head, node("p", turn.text));
    section.append(icon, body);
    transcript.append(section);
  }
}
function intro(title, text) {
  const box = node("div", null, "panel-intro");
  box.append(node("h3", title), node("p", text));
  return box;
}
function fields(entries) {
  const grid = node("dl", null, "metadata-grid");
  for (const [label, value] of entries) {
    const field = node("div", null, "data-field");
    field.append(node("dt", label), node("dd", value ?? "Not recorded", "mono"));
    grid.append(field);
  }
  return grid;
}
function cloudEvidence(call) {
  const section = node("section", null, "cloud-evidence");
  section.setAttribute("aria-label", "Cloud evidence");
  section.append(node("h3", "Cloud evidence"));
  const cloud = call.cloud;
  if (!cloud) {
    section.append(node("p", "No Cloud confirmation recorded for this call.", "context-note"));
    return section;
  }
  section.append(
    badge("Cloud session confirmed"),
    fields([
      ["Checked", date(cloud.checked_at)],
      ["Session ID", cloud.session_id],
      ["Cloud audio player", cloud.player_visible ? "Visible at check time" : "Not observed"],
      ["Listening review", call.review?.listened === true ? "Recorded" : "Pending"],
    ]),
    node(
      "p",
      "Cloud connection confirmed at the time shown. Listening review is separate.",
      "context-note",
    ),
  );
  const links = node("div", null, "cloud-evidence-links");
  links.append(link("View Cloud snapshot", cloud.screenshot_url));
  section.append(links);
  return section;
}
function renderProvenance(call) {
  const { pipeline: p, provenance: v } = call;
  $("provenance").replaceChildren(
    intro("Call details", "Connection, models, and settings."),
    cloudEvidence(call),
    node("h3", "Voice pipeline"),
    fields([
      ["Speech to text", p.stt],
      ["Language model", p.llm],
      ["Text to speech", p.tts],
      ["Voice ID", p.tts_voice],
      ["Turn detection", p.turn_detection],
      [
        "Endpointing",
        `${p.endpointing_mode} · ${p.min_delay ?? "?"}–${p.max_delay ?? "?"} seconds`,
      ],
    ]),
    node("h3", "Technical details"),
    fields([
      ["Git revision", v.git_revision],
      [
        "Working tree at call time",
        v.git_dirty === null
          ? "Not recorded"
          : v.git_dirty
            ? "Uncommitted changes present"
            : "Clean",
      ],
      ["Scenario version", v.scenario_version],
      ["LiveKit Agents SDK", v.sdk_version],
      ["Prompt SHA-256", v.prompt_sha256],
      ["Original recording SHA-256", call.recording.sha256],
    ]),
    node("p", "File fingerprint, not a signature or proof of correctness.", "context-note"),
  );
}
function renderGovernance(call) {
  const panel = $("governance");
  panel.replaceChildren(
    intro("Controls & data", "How this console handles calls and files."),
    fields([
      [
        "Console mode",
        state.controls ? "Calling enabled · confirmation required" : "Read-only · calling disabled",
      ],
      ["Call limits", "One at a time · fixed test destination · no automatic redial"],
      ["Saved files", "Local calls directory · original audio, transcript and metadata"],
      ["Provider processing", "LiveKit, Twilio and inference providers handle live calls."],
    ]),
    node(
      "p",
      "This viewer does not redact files or manage provider retention. Review content before sharing.",
      "context-note",
    ),
  );
  const recorded = [
    ["Claimed outcome", call?.claims?.claimed_state],
    ["Cross-call consistency", call?.claims?.consistency],
    ["Verified outcome", call?.claims?.verified_state],
  ].filter(([, value]) => value !== null && value !== undefined);
  if (recorded.length) {
    const details = node("details", null, "explanation");
    details.append(
      node("summary", "Recorded outcomes"),
      fields(
        recorded.map(([label, value]) => [
          label,
          typeof value === "string" ? value : JSON.stringify(value),
        ]),
      ),
    );
    panel.append(details);
  }
}
async function selectCall(id) {
  state.controller?.abort();
  const controller = new AbortController();
  state.controller = controller;
  state.selected = id;
  state.detail = null;
  $("audio").pause();
  $("call-content").hidden = true;
  $("review-panel").setAttribute("aria-busy", "true");
  emptyHeader("Loading call…", "Reading the original local artifacts.");
  renderList();
  if (state.view === "cards") {
    const card = $("call-list").querySelector('[aria-current="true"]');
    if (card) {
      const rail = $("call-list");
      const bounds = rail.getBoundingClientRect();
      const box = card.getBoundingClientRect();
      if (box.left < bounds.left) rail.scrollLeft -= bounds.left - box.left + 16;
      else if (box.right > bounds.right) rail.scrollLeft += box.right - bounds.right + 16;
    }
  }
  const timeout = setTimeout(() => controller.abort("timeout"), 12000);
  try {
    const call = await json(`/api/calls/${encodeURIComponent(id)}`, controller.signal);
    if (state.selected !== id || controller.signal.aborted) return;
    state.detail = call;
    renderHeader(call);
    renderConversation(call);
    renderReview(call, async (id) => {
      if (state.selected !== id) return;
      await refresh();
      const panel = $("listening-review").querySelector("details");
      if (panel) {
        panel.open = true;
        panel.querySelector("summary").focus();
      }
      $("announcement").textContent = "Review saved.";
    });
    renderProvenance(call);
    renderGovernance(call);
    $("call-content").hidden = false;
    selectTab("conversation");
    history.replaceState(null, "", `?call=${encodeURIComponent(id)}`);
    $("announcement").textContent =
      `${scenario(call.scenario)} loaded. ${call.turn_count} turns. ${outcome(call)[0]}.`;
  } catch (error) {
    if (controller !== state.controller) return;
    emptyHeader(
      "Call evidence unavailable",
      controller.signal.aborted ? "Loading timed out. Use Refresh calls to retry." : error.message,
    );
    $("announcement").textContent = "Call evidence unavailable. Refresh to retry.";
  } finally {
    clearTimeout(timeout);
    if (controller === state.controller) $("review-panel").setAttribute("aria-busy", "false");
  }
}
async function refresh() {
  $("refresh").disabled = true;
  $("global-error").hidden = true;
  $("call-list").setAttribute("aria-busy", "true");
  try {
    const data = await json("/api/calls", AbortSignal.timeout(12000));
    state.calls = data.calls;
    $("metric-pairs").textContent = data.calls.filter(
      (call) => call.recording.available && call.transcript_available,
    ).length;
    $("metric-reviewed").textContent =
      `${data.calls.filter((call) => call.review?.listened === true).length}/${data.calls.length}`;
    $("metric-usable").textContent = data.calls.filter((call) => call.review?.usable).length;
    renderList();
    if (data.truncated) {
      $("global-error").textContent =
        "Showing the most recent 1,000 call directories. Older calls remain on disk.";
      $("global-error").hidden = false;
    }
    const requested = state.selected || new URLSearchParams(location.search).get("call");
    const selected = data.calls.find((call) => call.call_id === requested) || data.calls[0];
    if (selected) await selectCall(selected.call_id);
    else {
      state.controller?.abort();
      state.selected = null;
      state.detail = null;
      $("audio").pause();
      $("audio").removeAttribute("src");
      $("audio").load();
      $("call-content").hidden = true;
      emptyHeader(
        "Your evidence starts here",
        "No calls have been saved in this directory. This read-only workspace will show them after collection.",
      );
      $("announcement").textContent = "No calls available.";
    }
  } catch (error) {
    $("global-error").textContent = `Could not refresh calls. ${error.message}`;
    $("global-error").hidden = false;
    if (!state.calls.length)
      $("call-list").replaceChildren(
        node("p", "Unable to load calls. Refresh to retry.", "empty-small"),
      );
  } finally {
    $("refresh").disabled = false;
    $("call-list").setAttribute("aria-busy", "false");
  }
}
document.addEventListener("console-mode", (event) => {
  state.controls = event.detail.enabled;
  renderGovernance(state.detail);
});
document.addEventListener("evidence-ready", () => refresh());
$("review-nav").addEventListener("click", () => {
  if (state.detail) {
    selectTab("conversation", true);
  } else {
    $("call-content").hidden = true;
    emptyHeader(
      "Your evidence starts here",
      "Select a call to review its recording, transcript, and provenance.",
    );
  }
});
for (const view of ["cards", "list"])
  $(`view-${view}`).addEventListener("click", () => setView(view));
setView(state.view);
$("call-list").addEventListener("scroll", railControls, { passive: true });
new ResizeObserver(railControls).observe($("call-list"));
for (const [id, direction] of [
  ["rail-prev", -1],
  ["rail-next", 1],
])
  $(id).addEventListener("click", () =>
    $("call-list").scrollBy({
      left: direction * $("call-list").clientWidth * 0.8,
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
    }),
  );
$("search-toggle").addEventListener("click", () => {
  if (!$("search-panel").hidden) return closeSearch(true);
  $("search-panel").hidden = false;
  $("search-toggle").setAttribute("aria-expanded", "true");
  const box = $("search-toggle").getBoundingClientRect();
  const panel = $("search-panel");
  panel.style.left = `${Math.max(12, Math.min(box.left, innerWidth - panel.offsetWidth - 12))}px`;
  panel.style.top = `${Math.max(12, Math.min(box.bottom + 8, innerHeight - panel.offsetHeight - 12))}px`;
  $("search").focus({ preventScroll: true });
});
$("search-close").addEventListener("click", () => closeSearch(true));
$("search-clear").addEventListener("click", () => {
  $("search").value = "";
  $("filter").value = "all";
  renderList();
  $("search").focus();
});
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".library-search")) closeSearch();
});
$("search-panel").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeSearch(true);
  }
});
window.addEventListener("resize", () => closeSearch());
$("search-panel").addEventListener("keydown", (event) => {
  // Safari may move focus to the document on a pointer press. Only keyboard
  // departure dismisses here; outside pointer presses have their own handler.
  if (event.key === "Tab")
    setTimeout(() => {
      if (!document.activeElement?.closest(".library-search")) closeSearch();
    }, 0);
});
document.addEventListener("operation-updated", (event) => {
  state.operation = event.detail;
  renderOperation();
});
$("search").addEventListener("input", renderList);
$("filter").addEventListener("change", renderList);
$("refresh").addEventListener("click", refresh);
$("audio").addEventListener("error", () => {
  if (!$("audio").getAttribute("src")) return;
  $("audio-error").textContent =
    "This recording could not be played. Check the file or try a browser that supports its audio format.";
  $("audio-error").hidden = false;
});
const tabs = [...document.querySelectorAll('[role="tab"]')];
for (const [index, tab] of tabs.entries()) {
  tab.addEventListener("click", () => selectTab(tab.getAttribute("aria-controls")));
  tab.addEventListener("keydown", (event) => {
    let target;
    if (event.key === "ArrowRight") target = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") target = (index + tabs.length - 1) % tabs.length;
    if (event.key === "Home") target = 0;
    if (event.key === "End") target = tabs.length - 1;
    if (target !== undefined && state.detail) {
      event.preventDefault();
      selectTab(tabs[target].getAttribute("aria-controls"), true);
    }
  });
}
$("governance-nav").addEventListener("click", () => {
  if (!state.detail) {
    emptyHeader("Workspace settings", "Local configuration and file handling.");
    renderGovernance(null);
    $("call-content").hidden = false;
  }
  selectTab("governance", true);
});
refresh();
