"""Validate a current GitHub label-name array supplied on stdin. No network or secrets."""

import json
import sys

TYPE_LABELS = {"type:task", "type:docs"}
AREA_LABELS = {
    "area:analysis",
    "area:ci",
    "area:evidence",
    "area:process",
    "area:simulator",
    "area:telephony",
    "area:ui",
}


def label_errors(value: object) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(label, str) for label in value):
        return ["Expected a JSON array of label names; label validation failed closed."]
    labels = set(value)
    kinds = {label for label in labels if label.startswith("type:")}
    errors = []
    if len(kinds) != 1 or not kinds <= TYPE_LABELS:
        errors.append("Require exactly one delivery type: type:task or type:docs.")
    if not labels & AREA_LABELS:
        errors.append("Require at least one area label: " + ", ".join(sorted(AREA_LABELS)) + ".")
    return errors


def main() -> int:
    try:
        value = json.load(sys.stdin)
    except (ValueError, OSError):
        print("Could not read current PR labels; label validation failed closed.", file=sys.stderr)
        return 1
    errors = label_errors(value)
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    print("PR label policy passed: one delivery type and at least one recognized area.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
