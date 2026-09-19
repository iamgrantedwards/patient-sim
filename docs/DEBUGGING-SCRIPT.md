# Debugging video — speaking notes

Prepared 2026-09-19 for issues #25 and #46. Use these as cues, pause to do the work,
and describe the actual results. The log and process structure were reviewed before
filming; the crash cause, regression and fix are still unresolved. No video has been
recorded as part of preparing these notes.

Record with your own voice, webcam and screen. The assessment gives no duration limit
for this debugging video; its separate final walkthrough is limited to three minutes.
Show the app, issue #46, the reviewed worker log and the AI/code workspace. Keep private
configuration out of the capture. Background detail and evidence are in [the journal](DEBUGGING.md).

## 1. What I built

I'm building a voice bot that acts as a patient and calls Pretty Good AI's test line.
It uses Python and LiveKit, with separate speech-to-text, language-model and
text-to-speech components. This interface lets me start a call and review the evidence.

## 2. What went wrong

Our first call connected and saved a conversation, although its ending needs review.
Our second attempt failed without saving a usable recording or transcript. The
interface stayed on Dialing until I stopped it. That's issue 46, and it's the problem
we're working on today.

## 3. What we learned before recording

During preparation, we opened the local worker log and mapped the running programs.
The application starts a managed agent server. LiveKit then starts a child process
inside that setup to run the patient conversation. These programs run on my Mac and
connect to LiveKit's cloud services.

The log shows a process crash, followed by another initialization encountering an
existing evidence file. We also found that our controller checks whether the managed
server is alive. That alone doesn't tell us whether its child conversation is alive.

That's a useful lead for the stuck status, but it doesn't explain the original crash.
We haven't reproduced the failure in a focused test or fixed it yet.

## 4. My first prompt

We are investigating issue 46. Before recording, we inspected the second attempt's
worker log and confirmed that LiveBackend.exited checks the managed server process,
not its child call job. The log shows a -11 exit followed by a FileExistsError during
later initialization. The original crash cause and reassignment mechanism remain unknown.

Validate those observations against the pinned SDK and our code. Separate the original
crash, repeated initialization, and stale UI status. Recommend the smallest offline
experiment to test the failure-propagation gap. Don't edit the implementation or place
a call yet.

[Pause. Show the response and explain which evidence supports the next step.]

## 5. Follow-up questions

Choose the question that fits what actually happened:

- Does this explain the original crash, or only the behavior afterward?
- Which part is confirmed by the code, and which part still needs a test?
- What would disprove that explanation?
- How can we reproduce the child failing while its parent stays alive?
- How do we prove the original evidence stays intact and no second call is started?

[Explain why you chose the question. Follow the actual findings, not a preset answer.]

## 6. When we're ready to test and fix

Let's write a focused regression for the behavior we've established and run it before
changing the implementation. Then make the smallest supported correction. Preserve the
original evidence, prevent duplicate dialing, and make the failure visible with proper
cleanup. Run the relevant checks and show what passed or still failed.

[Show the real failing result, change, verification and any follow-up iteration. If
we cannot reproduce it, explain that rather than claiming the test proved the cause.]

## 7. End this segment

We started with a failed call attempt. We have now established [what we actually learned].
We changed [the actual change, or say no fix yet]. We verified [the actual results].
What remains is [the unresolved question or next check].

If we corrected failure handling but haven't explained the original crash, those are
separate outcomes. I won't call the underlying crash solved based on that change alone.

If the live retest is still ahead: In the follow-up, we'll make one controlled call
and compare the recording, transcript and interface behavior. Automated checks alone
don't establish that the voice conversation works.

For the retest, use the [per-call checklist](CALL-REVIEW-TEMPLATE.md). Show the specific
before/after observation and next decision; narrating every checklist row is unnecessary.
The manual review sheet does not currently update the app badge.

## Follow-up recording

Last time, we established [finding] and made [change]. Since then, [state exactly what
work happened off camera, including the PR and test results]. Today we're verifying
[the specific remaining behavior].

[For a live retest, explicitly confirm one call. Observe the actual outcome, play the
recording and compare the transcript. A failed attempt is still a result to document.]

The result was [actual result]. This supports [the narrow conclusion]. It does not yet
establish [remaining uncertainty]. Our next step is [actual next action].

If recorded in separate parts, combine or clearly sequence them behind the submitted
debugging-video link. Check public access before submission. This document is speaking
notes, not evidence that any of these future steps has happened.
