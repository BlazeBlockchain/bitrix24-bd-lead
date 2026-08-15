#!/usr/bin/env python3
"""Sync the design tokens from design/tokens.css into both consumers.

web/src/index.css and extension/tokens.css used to carry the same token values
typed out by hand, with nothing to detect divergence. This script gives them a
single upstream and makes drift a test failure instead of a visual surprise
noticed three commits later.

It replaces ONLY the text between the markers, so each consumer keeps its own
hand-written rules. It does not parse CSS -- the extension tree must stay free
of dependencies, so this is textual region replacement plus targeted greps.

Usage:
    python3 scripts/sync_design_tokens.py            # rewrite both consumers
    python3 scripts/sync_design_tokens.py --check    # verify only, write nothing
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM = os.path.join(REPO_ROOT, "design", "tokens.css")
CONSUMERS = [
    os.path.join(REPO_ROOT, "web", "src", "index.css"),
    os.path.join(REPO_ROOT, "extension", "tokens.css"),
]

BEGIN = "/* >>> generated: design tokens -- edit design/tokens.css, run `make sync-tokens` */"
END = "/* <<< end generated */"

# The palette this design pass retires. If any of these reappears in a consumer,
# some surface has quietly drifted back to the old look. Checking for them is
# what turns "the legacy palette is retired" from an intention into a test.
LEGACY_VALUES = [
    "#f97316",  # old accent (orange)
    "#0d1117",  # old bg
    "#161b22",  # old surface
    "#1c2330",  # old surface-2
    "#30363d",  # old border
    "#e6edf3",  # old text
    "#8b949e",  # old muted
    "#38bdf8",  # old accent-2
    "#4ade80",  # old accent-3
    "#f87171",  # old danger
    "249, 115, 22",  # the hard-coded orange focus ring, in rgba() form
    "249,115,22",
]


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def upstream_tokens() -> str:
    """Everything from the first :root onward -- the header comment stays home."""
    text = read(UPSTREAM)
    index = text.find(":root")
    if index == -1:
        sys.exit(f"{UPSTREAM}: no :root block found")
    return text[index:].strip()


def split_consumer(path: str, text: str) -> tuple[str, str, str]:
    """Return (before, generated_region, after), validating the markers."""
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        sys.exit(
            f"{rel(path)}: expected exactly one BEGIN and one END marker "
            f"(found {text.count(BEGIN)} and {text.count(END)}).\n"
            f"  BEGIN: {BEGIN}\n  END:   {END}\n"
            "A missing marker means this file would drift forever undetected."
        )
    head, rest = text.split(BEGIN, 1)
    body, tail = rest.split(END, 1)
    if text.index(BEGIN) > text.index(END):
        sys.exit(f"{rel(path)}: END marker appears before BEGIN marker")
    return head + BEGIN, body, END + tail


def rel(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT)


def legacy_hits(path: str, text: str) -> list[str]:
    problems = []
    for value in LEGACY_VALUES:
        for number, line in enumerate(text.splitlines(), start=1):
            if value in line:
                problems.append(
                    f"{rel(path)}:{number}: retired palette value {value!r} -> {line.strip()}"
                )
    return problems


def shadowed_tokens(path: str, tokens: str, outside: str) -> list[str]:
    """A token redefined outside the generated region silently wins over it."""
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", tokens))
    problems = []
    for number, line in enumerate(outside.splitlines(), start=1):
        match = re.match(r"\s*(--[a-z0-9-]+)\s*:", line)
        if match and match.group(1) in declared:
            problems.append(
                f"{rel(path)}: {match.group(1)} is redefined outside the generated "
                "region and shadows the upstream value"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the consumers match the upstream; write nothing",
    )
    args = parser.parse_args()

    if not os.path.exists(UPSTREAM):
        sys.exit(f"Missing upstream {rel(UPSTREAM)}")

    tokens = upstream_tokens()
    expected = f"\n{tokens}\n"
    problems: list[str] = []
    changed: list[str] = []

    for path in CONSUMERS:
        if not os.path.exists(path):
            problems.append(f"{rel(path)}: missing")
            continue

        text = read(path)
        head, body, tail = split_consumer(path, text)

        if args.check:
            if body != expected:
                diff = difflib.unified_diff(
                    expected.splitlines(),
                    body.splitlines(),
                    fromfile=f"{rel(UPSTREAM)} (expected)",
                    tofile=f"{rel(path)} (actual)",
                    lineterm="",
                )
                problems.append(
                    f"{rel(path)}: token region has drifted from the upstream\n"
                    + "\n".join(f"    {line}" for line in diff)
                )
        elif body != expected:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(head + expected + tail)
            changed.append(rel(path))

        current = read(path)
        _, region, _ = split_consumer(path, current)
        outside = current.replace(region, "\n")
        problems.extend(legacy_hits(path, outside))
        problems.extend(shadowed_tokens(path, tokens, outside))

    if problems:
        header = "Token check FAILED:" if args.check else "Token sync completed WITH PROBLEMS:"
        print(f"\n{header}", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.check:
        print(f"Tokens in sync: {', '.join(rel(p) for p in CONSUMERS)}")
    elif changed:
        print("Updated: " + ", ".join(changed))
    else:
        print("Already in sync; nothing to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
