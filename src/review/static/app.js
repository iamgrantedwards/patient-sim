const $ = (id) => document.getElementById(id);
const state = { calls: [], selected: null, detail: null, controller: null, controls: false };

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = String(text);
  if (className) element.className = className;
  return element;
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
function scenario(value) {
  if (["smoke", "calibration"].includes(value)) return "Office information";
  return value?.replaceAll("_", " ") || "Unknown scenario";
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
function renderList() {
  const query = $("search").value.trim().toLowerCase();
  const filter = $("filter").value;
  const calls = state.calls.filter((call) => {
    const matches = `${scenario(call.scenario)} ${call.call_id} ${call.ended_by}`
      .toLowerCase()
      .includes(query);
    return (
      matches &&
      (filter === "all" ||
        (filter === "pending" && call.recording.listened_by_human !== true) ||
        (filter === "partial" && call.partial_turns > 0) ||
        (filter === "missing" && (!call.recording.available || !call.transcript_available)))
    );
  });
  $("library-count").textContent = `${calls.length} ${calls.length === 1 ? "call" : "calls"}`;
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
    return;
  }
  for (const call of calls) {
    const button = node("button", null, "call-card");
    button.type = "button";
    button.setAttribute("aria-current", String(state.selected === call.call_id));
    button.setAttribute(
      "aria-label",
      `${scenario(call.scenario)} · ${call.call_id} · ${outcome(call)[0]}`,
    );
    const top = node("div", null, "card-top");
    top.append(
      node("h3", scenario(call.scenario)),
      node("span", duration(call.duration_seconds), "duration mono"),
    );
    button.append(
      top,
      node("p", date(call.started_at, true)),
      node("p", call.call_id, "call-id mono"),
      badge(...outcome(call)),
    );
    button.addEventListener("click", () => selectCall(call.call_id));
    $("call-list").append(button);
  }
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
  title.append(
    node("div", "RECORDED CONVERSATION", "detail-kicker"),
    node("h2", scenario(call.scenario)),
  );
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
  if (call.recording.listened_by_human !== true) {
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
      ["Listening review", call.recording.listened_by_human === true ? "Recorded" : "Pending"],
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
function control(title, status, summary, text, variant = "neutral", source) {
  const row = node("div", null, "control-row");
  const heading = node("div", null, "control-heading");
  heading.append(node("h4", title), badge(status, variant));
  row.append(heading, node("p", summary));
  const details = node("details", null, "explanation");
  const trigger = node("summary", "Details");
  trigger.setAttribute("aria-label", `Details: ${title}`);
  details.append(trigger, node("p", text));
  if (source) details.append(link(source[0], source[1]));
  row.append(details);
  return row;
}
function claimText(value) {
  if (value === null || value === undefined) return "Not established";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
function renderGovernance(call) {
  const panel = $("governance");
  const claims = node("div", null, "claims");
  for (const [label, key] of [
    ["What was claimed", "claimed_state"],
    ["Cross-call consistency", "consistency"],
    ["Independently verified", "verified_state"],
  ]) {
    const item = node("div", null, "claim");
    item.append(node("h4", label), node("p", claimText(call?.claims?.[key])));
    claims.append(item);
  }
  const controls = node("div", null, "governance-list");
  controls.append(
    control(
      "Human oversight",
      call?.recording.listened_by_human === true ? "Review recorded" : "Review pending",
      "Listen to the full call before accepting evidence or publishing findings.",
      "A person must listen to the recording and validate evidence before publishing findings. This read-only view cannot approve a call or mark it reviewed.",
      "warning",
    ),
    control(
      "Purpose & scope",
      "Defined",
      "Synthetic assessment calls only. No patient care or clinical decisions.",
      "A synthetic patient tests an explicitly designated assessment line. This system does not deliver patient care or make clinical decisions. Unknown patient facts must not be invented.",
    ),
    control(
      "Privacy & publication",
      "Manual gate",
      "Review recordings before publication. Synthetic inputs can still produce personal information.",
      "Synthetic inputs do not guarantee that returned audio is free of personal information. Inspect recordings and transcripts before public release. Redaction was disabled for evidence capture; the viewer does not redact or anonymize content.",
      "warning",
    ),
    control(
      "Local review boundary",
      state.controls ? "Calling enabled" : "Read-only",
      state.controls
        ? "Calls require confirmation; evidence stays unchanged."
        : "Local, read-only evidence review. No calls can be placed here.",
      state.controls
        ? "Evidence routes are read-only. Calling was explicitly enabled for this process: confirmed start/stop requests use a local session token, exact Origin checks, one shared call slot, and the fixed assessment destination. Provider credentials stay on the server."
        : "Read-only routes, loopback binding, restricted file access, and browser security headers. The viewer loads no telephony credentials, sends no analytics, and makes no model calls.",
    ),
    control(
      "AI instructions & untrusted content",
      "Bounded",
      "Transcripts are treated as data. Code enforces the fixed call destination.",
      "Transcript content is rendered as text, never executed as HTML or passed to an automated judge. The caller’s fixed destination is enforced in code; prompts alone are not a security boundary.",
      "neutral",
      ["OWASP: prompt injection ↗", "https://genai.owasp.org/llmrisk/llm01-prompt-injection/"],
    ),
    control(
      "Data lifecycle & provider processing",
      "Open obligations",
      "Calls use external providers. Retention and deletion obligations remain open.",
      "The original calls use LiveKit, Twilio, and inference providers. Local review is not a claim that all call data stays on-device. Provider retention, access, consent, and deletion obligations need separate review before use beyond this assessment.",
      "warning",
    ),
  );
  const sources = node("div", null, "link-row");
  sources.append(
    link(
      "NIST AI Risk Management Framework ↗",
      "https://www.nist.gov/itl/ai-risk-management-framework",
    ),
    link(
      "HHS de-identification guidance ↗",
      "https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html",
    ),
  );
  panel.replaceChildren(
    intro(
      "Evidence, oversight, and limits",
      "NIST AI RMF informs these controls; not a certification or a claim of HIPAA compliance.",
    ),
    claims,
    controls,
    sources,
    node("p", "Production use requires a separate legal and institutional review.", "context-note"),
  );
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
  const timeout = setTimeout(() => controller.abort("timeout"), 12000);
  try {
    const call = await json(`/api/calls/${encodeURIComponent(id)}`, controller.signal);
    if (state.selected !== id || controller.signal.aborted) return;
    state.detail = call;
    renderHeader(call);
    renderConversation(call);
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
    $("metric-calls").textContent = data.calls.length;
    $("metric-pairs").textContent = data.calls.filter(
      (call) => call.recording.available && call.transcript_available,
    ).length;
    $("metric-reviewed").textContent =
      `${data.calls.filter((call) => call.recording.listened_by_human === true).length}/${data.calls.length}`;
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
    emptyHeader("AI governance", "Safeguards and data handling.");
    renderGovernance(null);
    $("call-content").hidden = false;
  }
  selectTab("governance", true);
});
refresh();
