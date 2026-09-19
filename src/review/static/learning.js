// Browser-only help. No call requests, evidence writes, or external services.
const topics = {
  calling: [
    "Run a test call",
    "Our simulated patient calls the assessment agent. Review & call opens a confirmation; only Place one call starts it. Live text appears here, and audio is available afterward.",
  ],
  scenario: [
    "Scenario",
    "A scenario gives the patient a goal. Office information asks about hours, location and insurance without changing appointments.",
  ],
  attempts: [
    "Call attempts",
    "Saved attempts include failed and incomplete calls. This count is not the number of complete, reviewed conversations.",
  ],
  pairs: [
    "Audio + transcript",
    "Both files are available. Listen and compare them before counting a call as a complete, usable conversation.",
  ],
  review: [
    "Listening review",
    "Reviews recorded in the call metadata. Playing audio does not mark a call reviewed. A person must check the full recording against the transcript.",
  ],
  library: [
    "Calls",
    "Choose a saved attempt to review below. Each call has its own ID, even when several use the same scenario. New results appear after finalization.",
  ],
  conversation: [
    "Conversation",
    "Listen to both sides and follow the transcript for the selected call. Incomplete speech is kept visible so you can judge the ending.",
  ],
  provenance: [
    "Provenance",
    "The models, settings, prompt fingerprint and code version saved with this call. Use these to understand what changed between experiments. Cloud evidence is a dated check for this call, separate from listening review.",
  ],
  governance: [
    "Controls & data",
    "See the current console mode, enforced call limits, local files and external providers. Broader governance recommendations live in the project documentation.",
  ],
  recording: [
    "Call recording",
    "The original saved audio, played only when you choose. A readable file can still contain silence, overlap or an incomplete ending; listen all the way through.",
  ],
  transcript: [
    "Conversation transcript",
    "Text from the conversation, including partial speech. Speech recognition can be wrong. Compare it with the audio; turn numbers are not timestamps.",
  ],
};
const byId = (id) => document.getElementById(id);
const toggle = byId("learning-toggle");
const tooltip = byId("learning-tooltip");
const preference = "patient-sim.learning.v1";
let enabled = false;
let active = null;
let closeTimer;
try {
  enabled = localStorage.getItem(preference) === "on";
} catch {
  // Help remains usable when the browser blocks storage.
}

function hide() {
  clearTimeout(closeTimer);
  if (active) {
    const descriptions = (active.getAttribute("aria-describedby") || "")
      .split(" ")
      .filter((id) => id && id !== tooltip.id);
    if (descriptions.length) active.setAttribute("aria-describedby", descriptions.join(" "));
    else active.removeAttribute("aria-describedby");
  }
  active = null;
  if (tooltip.matches(":popover-open")) tooltip.hidePopover();
}
function show(trigger) {
  if (!enabled || !trigger || !topics[trigger.dataset.helpKey]) return;
  hide();
  active = trigger;
  const [title, description] = topics[trigger.dataset.helpKey];
  byId("learning-tooltip-title").textContent = title;
  byId("learning-tooltip-text").textContent = description;
  const descriptions = trigger.getAttribute("aria-describedby");
  trigger.setAttribute("aria-describedby", [descriptions, tooltip.id].filter(Boolean).join(" "));
  tooltip.showPopover();
  position();
}
function position() {
  if (!active) return;
  const box = active.getBoundingClientRect();
  const tip = tooltip.getBoundingClientRect();
  tooltip.style.left = `${Math.max(12, Math.min(box.left, innerWidth - tip.width - 12))}px`;
  const below = box.bottom + 8;
  tooltip.style.top = `${Math.max(12, Math.min(below + tip.height > innerHeight - 12 ? box.top - tip.height - 8 : below, innerHeight - tip.height - 12))}px`;
}
function later() {
  clearTimeout(closeTimer);
  closeTimer = setTimeout(() => {
    if (document.activeElement !== active && !tooltip.matches(":hover")) hide();
  }, 180);
}
function register(trigger, key) {
  trigger.dataset.helpKey = key;
  trigger.addEventListener("pointerenter", (event) => {
    if (event.pointerType === "mouse") show(trigger);
  });
  trigger.addEventListener("pointerleave", later);
  trigger.addEventListener("focus", () => show(trigger));
  trigger.addEventListener("blur", later);
  trigger.addEventListener("click", () => {
    trigger.focus({ preventScroll: true });
    show(trigger);
  });
}
function mount() {
  if (active && !active.isConnected) hide();
  for (const anchor of document.querySelectorAll("[data-learn]:not([data-learn-mounted])")) {
    const key = anchor.dataset.learn;
    if (!topics[key]) continue;
    anchor.dataset.learnMounted = "true";
    if (anchor.matches("button")) {
      register(anchor, key); // Tabs retain their normal action and keyboard behavior.
      continue;
    }
    const hint = document.createElement("button");
    hint.type = "button";
    hint.className = "learn-hint";
    hint.textContent = "?";
    hint.setAttribute("aria-label", `Help: ${topics[key][0]}`);
    if (anchor.matches("span")) anchor.append(hint);
    else {
      const wrapper = document.createElement("div");
      wrapper.className = "learn-anchor";
      anchor.before(wrapper);
      wrapper.append(anchor, hint);
    }
    register(hint, key);
  }
}
function render() {
  document.documentElement.classList.toggle("learning-enabled", enabled);
  toggle.setAttribute("aria-pressed", String(enabled));
  byId("learning-note").hidden = !enabled;
  if (!enabled) hide();
}
toggle.addEventListener("click", () => {
  enabled = !enabled;
  render();
  byId("learning-announcement").textContent = enabled
    ? "Learning mode on. Help is available by hover, keyboard focus or tap."
    : "Learning mode off.";
  try {
    localStorage.setItem(preference, enabled ? "on" : "off");
  } catch {
    // The preference simply lasts for this page when storage is unavailable.
  }
});
tooltip.addEventListener("pointerenter", () => clearTimeout(closeTimer));
tooltip.addEventListener("pointerleave", later);
document.addEventListener("pointerdown", (event) => {
  if (active && !active.contains(event.target) && !tooltip.contains(event.target)) hide();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && active) {
    event.preventDefault();
    event.stopPropagation();
    hide();
  }
});
window.addEventListener("resize", position);
document.addEventListener("scroll", position, true);
mount();
new MutationObserver(mount).observe(byId("main"), { childList: true, subtree: true });
render();

// A local manual, available independently of whether contextual hints are enabled.
const guide = byId("learning-guide");
const guideOpen = byId("learning-guide-open");
guideOpen.addEventListener("click", () => {
  hide();
  guide.showModal();
  guide.scrollTop = 0;
  byId("learning-guide-close").focus({ preventScroll: true });
});
byId("learning-guide-close").addEventListener("click", () => guide.close());
guide.addEventListener("close", () => guideOpen.focus({ preventScroll: true }));

// Keep keyboard navigation in the manual, including at its first and last controls.
guide.addEventListener("keydown", (event) => {
  if (event.key !== "Tab") return;
  const stops = [...guide.querySelectorAll("button, summary, a[href]")].filter(
    (element) => !element.disabled && element.getClientRects().length > 0,
  );
  const first = stops[0];
  const last = stops.at(-1);
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

// Icon labels are also exposed to screen readers; Escape dismisses visual labels.
for (const button of document.querySelectorAll(".icon-button")) {
  button.addEventListener("keydown", (event) => {
    if (event.key === "Escape") button.classList.add("tip-dismissed");
  });
  for (const event of ["pointerenter", "focus"])
    button.addEventListener(event, () => button.classList.remove("tip-dismissed"));
}
