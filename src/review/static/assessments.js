const labels = {
  request_handling: "Request handling",
  consistency: "Consistency",
  clarification: "Clarification",
  supported_claims: "Supported claims",
  next_steps: "Next steps",
};
function el(tag, text, cls) {
  const item = document.createElement(tag);
  if (text != null) item.textContent = text;
  if (cls) item.className = cls;
  return item;
}
function citations(items, call) {
  const list = el("div", null, "assessment-citations");
  for (const item of items) {
    const button = el("button", `Turn ${item.turn + 1} · “${item.quote}”`, "assessment-citation");
    button.type = "button";
    button.addEventListener("click", () => {
      const transcript = document.getElementById("conversation-transcript");
      transcript.open = true;
      const turn = [...document.querySelectorAll("#transcript .turn")].find(
        (row) => row.dataset.turn === String(item.turn),
      );
      if (turn) {
        turn.scrollIntoView({ block: "center", behavior: "instant" });
        turn.focus({ preventScroll: true });
      }
      const source = call.turns.find((t) => t.idx === item.turn);
      if (Number.isFinite(source?.audio_start_ms) && call.recording.available)
        document.getElementById("audio").currentTime = source.audio_start_ms / 1000;
    });
    list.append(button);
  }
  return list;
}
export async function renderAssessment(call) {
  const target = document.getElementById("ai-assessment");
  const panel = el("details", null, "assessment-panel");
  const heading = el("summary");
  const status = el("span", "Loading…", "assessment-status");
  heading.append(el("span", "AI assessment"), status);
  const body = el("div", null, "assessment-body");
  panel.append(heading, body);
  target.replaceChildren(panel);
  const url = `/api/calls/${encodeURIComponent(call.call_id)}/assessment`;
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error();
    const state = await response.json();
    if (target.contains(panel)) draw(state);
  } catch {
    status.textContent = "Unavailable";
    body.append(el("p", "Assessment could not load. Select the call again to retry."));
  }
  function draw(state) {
    body.replaceChildren();
    const saved = state.latest;
    status.textContent =
      state.status === "stale"
        ? "Evidence changed · reassess"
        : state.status === "unavailable"
          ? "Unavailable"
          : state.score
            ? `${state.score.percent == null ? "Limited coverage" : `${state.score.percent}/100`} · provisional`
            : "Not assessed";
    body.append(
      el(
        "p",
        "Transcript analysis of the assessment agent. Confirm observations against the recording; listening review stays separate.",
        "context-note",
      ),
    );
    if (saved) {
      if (state.status === "stale")
        body.append(
          el(
            "p",
            "This result belongs to earlier evidence or settings. Its score is withheld.",
            "notice",
          ),
        );
      body.append(el("p", saved.result.summary, "assessment-summary"));
      const grid = el("div", null, "assessment-scores");
      for (const dimension of saved.result.dimensions) {
        const row = el("details", null, "assessment-dimension");
        const summary = el("summary");
        summary.append(
          el("span", labels[dimension.dimension]),
          el("strong", dimension.score == null ? "N/A" : `${dimension.score}/2`),
        );
        row.append(summary, el("p", dimension.rationale), citations(dimension.evidence, call));
        grid.append(row);
      }
      body.append(grid);
      body.append(
        el(
          "p",
          "2 · No material issue observed   1 · Minor gap   0 · Substantial issue   N/A · Not assessable",
          "context-note",
        ),
      );
      if (state.score)
        body.append(
          el(
            "p",
            `${state.score.assessed}/5 dimensions assessed. Overall score requires at least three; unassessed dimensions are excluded.`,
            "context-note",
          ),
        );
      body.append(el("h4", `Observations · ${saved.result.observations.length}`));
      if (!saved.result.observations.length)
        body.append(
          el(
            "p",
            "No specific concerns identified in this transcript. This does not verify audio quality or backend outcomes.",
            "context-note",
          ),
        );
      for (const observation of saved.result.observations) {
        const item = el("details", null, "assessment-observation");
        item.append(el("summary", observation.title));
        item.append(
          el("p", `Attribution: ${observation.attribution} · Needs confirmation`, "context-note"),
        );
        for (const [label, value] of [
          ["Expected", observation.expected_behavior],
          ["Basis", observation.basis_for_expectation],
          ["Uncertainty", observation.uncertainty],
          ["Suggested improvement", observation.recommended_improvement],
          ["Next test", observation.next_test],
        ]) {
          const line = el("p");
          line.append(el("strong", `${label}: `), document.createTextNode(value));
          item.append(line);
        }
        item.append(citations(observation.evidence, call));
        body.append(item);
      }
      body.append(
        el(
          "p",
          `${saved.model} · ${saved.rubric} · ${new Date(saved.created_at).toLocaleString()}`,
          "context-note assessment-provenance",
        ),
      );
    }
    if (!state.enabled) {
      body.append(
        el(
          "p",
          state.status === "unavailable"
            ? "Saved assessment cannot be read. Original files are preserved."
            : "Read-only. Enable assessments when starting the local app to analyze a call.",
          "context-note",
        ),
      );
    } else if (!state.eligible) {
      body.append(
        el(
          "p",
          "Insufficient evidence. A finished conversation with both speakers and a recording is required; no agent score is assigned.",
          "notice",
        ),
      );
    } else if (state.status !== "saved") {
      const button = el(
        "button",
        saved ? "Reassess transcript" : "Assess transcript",
        "button primary",
      );
      button.type = "button";
      const feedback = el(
        "p",
        "Sends this transcript to LiveKit Inference. Uses your account credits; no phone call is made.",
        "context-note",
      );
      feedback.setAttribute("role", "status");
      body.append(button, feedback);
      button.addEventListener("click", async () => {
        button.disabled = true;
        button.textContent = "Assessing…";
        feedback.textContent = "Checking the transcript and linking supporting evidence…";
        try {
          const response = await fetch(url, {
            method: "POST",
            headers: { "X-Assessment-Token": state.token },
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || "Assessment failed.");
          if (target.contains(panel)) draw(result);
        } catch (error) {
          feedback.textContent =
            error.message || "Could not assess. Reopen the call to check its status.";
          button.textContent = "Retry assessment";
          button.disabled = false;
        }
      });
    }
  }
}
