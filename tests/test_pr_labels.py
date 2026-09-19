"""Metadata is a merge gate, including after an earlier successful check."""

import io
import json
import runpy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-pr-labels.py"
policy = runpy.run_path(str(SCRIPT))


@pytest.mark.parametrize(
    "labels, allowed",
    [
        (["type:task", "area:ui", "bug"], True),
        (["type:docs", "area:process", "area:ci"], True),
        (["type:task", "area:ci"], True),  # Dependabot uses the same policy.
        ([], False),
        (["type:task"], False),  # Removing the area after a pass must block.
        (["area:ui"], False),
        (["type:docs", "type:task", "area:ui"], False),
        (["type:finding", "area:analysis"], False),  # Findings belong to issues.
        (["type:task", "area:typo"], False),
        ({"labels": ["type:task", "area:ui"]}, False),
        (["type:task", None], False),
    ],
)
def test_label_policy(labels, allowed):
    assert (policy["label_errors"](labels) == []) is allowed


@pytest.mark.parametrize(
    "raw, expected",
    [
        (json.dumps(["type:task", "area:ui"]), 0),
        (json.dumps(["type:task"]), 1),
        ("not a JSON response", 1),
    ],
)
def test_cli_exit_status(monkeypatch, capsys, raw, expected):
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))
    assert policy["main"]() == expected
    output = capsys.readouterr()
    assert bool(output.err) is (expected != 0)
