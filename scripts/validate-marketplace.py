#!/usr/bin/env python3
"""Validate the marketplace manifest.

A broken manifest breaks `plugin install` for everyone, and the author is the
last to notice — nothing here is exercised locally. So this runs in CI on every
push, and is worth running by hand before one.

Checked:
  - the JSON parses, and carries the keys Claude Code reads
  - plugin names are unique (the name is the install coordinate)
  - every source URL is a well-formed https/git URL
  - with --network, each referenced repository actually resolves
"""
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"
URL_RE = re.compile(r"^https://[\w.-]+/[\w.-]+/[\w.-]+?(\.git)?$")


def main() -> int:
    check_network = "--network" in sys.argv
    errors: list[str] = []

    try:
        data = json.loads(MANIFEST.read_text())
    except FileNotFoundError:
        print(f"FAIL  no manifest at {MANIFEST}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL  manifest is not valid JSON: {exc}")
        return 1

    if not data.get("name"):
        errors.append("manifest has no `name` — this is the marketplace's identity")
    if not isinstance(data.get("plugins"), list) or not data["plugins"]:
        errors.append("manifest has no `plugins` list")
        for line in errors:
            print(f"FAIL  {line}")
        return 1

    seen: set[str] = set()
    for i, plugin in enumerate(data["plugins"]):
        label = plugin.get("name") or f"plugins[{i}]"

        if not plugin.get("name"):
            errors.append(f"{label}: missing `name`")
        elif plugin["name"] in seen:
            errors.append(f"{label}: duplicate name — install would be ambiguous")
        else:
            seen.add(plugin["name"])

        if not plugin.get("description"):
            errors.append(f"{label}: missing `description`")

        source = plugin.get("source")
        if not isinstance(source, dict) or "url" not in source:
            errors.append(f"{label}: `source` must be an object carrying a `url`")
            continue

        url = source["url"]
        if not URL_RE.match(url):
            errors.append(f"{label}: `{url}` is not a well-formed https repo URL")
            continue

        if check_network:
            # ls-remote rather than a plain fetch: it answers for a private or
            # renamed repo without cloning anything.
            probe = subprocess.run(
                ["git", "ls-remote", "--exit-code", url, "HEAD"],
                capture_output=True,
                timeout=30,
            )
            if probe.returncode != 0:
                errors.append(f"{label}: `{url}` does not resolve")

    for line in errors:
        print(f"FAIL  {line}")
    if errors:
        return 1

    scope = "reachable" if check_network else "well-formed"
    print(f"ok    {data['name']}: {len(seen)} plugins, all {scope}")
    for name in sorted(seen):
        print(f"      {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
