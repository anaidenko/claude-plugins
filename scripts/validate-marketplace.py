#!/usr/bin/env python3
"""Validate the marketplace manifest.

A broken manifest breaks `plugin install` for everyone, and the author is the
last to notice — nothing here is exercised locally. So this runs in CI on every
push, and is worth running by hand before one.

Checked:
  - the JSON parses, and carries the keys Claude Code reads
  - plugin names are unique (the name is the install coordinate)
  - every source is a well-formed npm package name or https/git URL
  - an npm source pins no version, so users always get `latest`
  - with --network, each source actually resolves; for npm, `latest` is a
    stable version whose tarball carries a plugin.json of the same name
"""
import io
import json
import re
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "marketplace.json"
URL_RE = re.compile(r"^https://[\w.-]+/[\w.-]+/[\w.-]+?(\.git)?$")
NPM_RE = re.compile(r"^(@[a-z0-9][\w.-]*/)?[a-z0-9][\w.-]*$")
REGISTRY = "https://registry.npmjs.org/"


def fetch(url: str, accept: str = "*/*") -> bytes:
    request = urllib.request.Request(url, headers={"Accept": accept})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def check_npm_package(label: str, name: str, package: str) -> list[str]:
    """What a user's install would hit: the version `latest` points at."""
    try:
        doc = json.loads(fetch(
            REGISTRY + urllib.parse.quote(package, safe="@"),
            # The abbreviated document: dist-tags and tarball links, no READMEs.
            "application/vnd.npm.install-v1+json",
        ))
    except Exception as exc:  # noqa: BLE001 — any failure means "does not resolve"
        return [f"{label}: npm package `{package}` does not resolve ({exc})"]

    latest = doc.get("dist-tags", {}).get("latest")
    if not latest:
        return [f"{label}: `{package}` has no `latest` version on npm"]
    # A first publish briefly tags a `0.0.0-stage` placeholder as latest, and a
    # release candidate published without `--tag next` would land there too.
    # Either would ship to every user, so a prerelease here is an error.
    if "-" in latest:
        return [f"{label}: `{package}@latest` is the prerelease {latest}"]

    try:
        tarball = fetch(doc["versions"][latest]["dist"]["tarball"])
        with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
            member = archive.extractfile("package/.claude-plugin/plugin.json")
            manifest = json.load(member)
    except KeyError:
        return [f"{label}: `{package}@{latest}` has no .claude-plugin/plugin.json"]
    except Exception as exc:  # noqa: BLE001
        return [f"{label}: could not read `{package}@{latest}` ({exc})"]

    if manifest.get("name") != name:
        return [f"{label}: `{package}@{latest}` is the plugin `{manifest.get('name')}`"]
    return []


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
        kind = source.get("source") if isinstance(source, dict) else None

        if kind == "npm":
            package = source.get("package", "")
            if not NPM_RE.match(package):
                errors.append(f"{label}: `{package}` is not a well-formed npm package name")
                continue
            if "version" in source:
                errors.append(f"{label}: npm source pins `version` — omit it so users get `latest`")
                continue
            if check_network:
                errors.extend(check_npm_package(label, plugin.get("name"), package))
            continue

        if kind != "url" or "url" not in source:
            errors.append(f"{label}: `source` must be an npm package or a `url` source")
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
