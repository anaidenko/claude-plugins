# Maintaining the marketplace

This repository holds only the marketplace manifest,
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Each
plugin lives in its own repository and is installed from its npm package, so
plugins release on their own schedule, and adding a plugin here does not affect
installs of the others.

## Why npm, not the git repo

Until 2026-11-16 the entries pointed at each repo by URL. They point at npm now
for two reasons:

- **Only a published release reaches users.** A git source served whatever
  `main` held, so a pushed commit was live before its tag, its npm version and
  its GitHub Release existed.
- **Installs count as npm downloads.** npm's search ranks a package with zero
  downloads below everything else, even for its exact name, and installs through
  git never showed up in the count.

Checked before the switch, in an isolated `CLAUDE_CONFIG_DIR`: an npm install
lands in the same `cache/anaidenko/<plugin>/<version>/` as a git one, with the
package root as the plugin root and file modes intact. An existing git install
at the current version stays as it is. The next version replaces it from npm.

## Validating

Validate any edit before pushing — a broken manifest breaks `plugin install`
for everyone, and nothing here runs locally:

```bash
python3 scripts/validate-marketplace.py --network
```

CI runs the same check on every push, and weekly: a package can be deprecated,
or its `latest` tag moved, without a commit landing here. With `--network` it
reads what a user's install would get: `latest` must be a stable version whose
tarball carries a `plugin.json` of the same name.

## Adding a plugin

Append an entry with `name`, `description`, and a `source` naming its npm
package:

```json
{
    "name": "my-plugin",
    "source": { "source": "npm", "package": "@anaidenko/my-plugin" },
    "description": "One line, shown in the plugin browser."
}
```

The `name` is the install coordinate (`my-plugin@anaidenko`) and must match the
plugin's own `.claude-plugin/plugin.json`. Add it to the list in the README
too. Leave out `version`: without it every user gets `latest`, and the
validator rejects a pinned one.

The plugin repo also takes the shared installer and release pipeline (see
[Shared across the plugin repos](#shared-across-the-plugin-repos)), and its
first npm publish is made by hand before CI can take over: the release skill's
*First publish* walks through it. **Add the entry only after that first release
is npm's `latest`.** During a first publish npm tags a `0.0.0-stage`
placeholder as `latest` for a couple of minutes, and the release candidate goes
out under `next`; an entry added earlier would install either one.

The package's `files` must carry everything the plugin runs: the tarball *is*
the installed plugin, and nothing outside it reaches users.

## Releasing a plugin

Nothing to do here. Each plugin repo releases with its own `/release` skill: a
version tag runs that repo's `publish.yml`, which publishes to npm and then
creates the GitHub Release. This manifest deliberately carries no `version`
fields; the installed version is read from the package's `plugin.json`.

Mind what reaches users when: the marketplace installs npm's `latest`, so a
release reaches users once `publish.yml` has published it, and not before.
Pushing `main` alone changes nothing for them. Anything published to npm
without `--tag next`, a release candidate included, becomes `latest` and goes
to every user.

## Renaming or moving a plugin repo

Nothing to change here: the entry names the npm package, not the repo. Update
the package's npm trusted publisher, which names the repository, or the next
release fails to publish. Also update `homepage` in its `package.json`, which
the installer prints.

A renamed npm *package* does need its entry here updated in the same pass. The
old name keeps serving its last version until then.

## Changing a plugin's description

It lives in four places: the manifest here (the plugin browser), the README
here, the plugin's `plugin.json`, and its `package.json` (the npm page). They
need not match word for word, but should say the same thing; the plugin's own
README is separate again.

## Shared across the plugin repos

Some files are copied into every plugin repo rather than shared, so a change to
one is a change to all, in the same pass:

- `.github/workflows/publish.yml`, byte for byte. It reads every name from the
  manifests. It stays a copy rather than a reusable workflow called from here:
  npm Trusted Publishing is set up per workflow file, and npm does not document
  publishing from a `workflow_call` workflow — a failure would only show on a
  real release.
- `bin/<plugin>.js`, everything above the `── This plugin` marker: the `npx`
  installer's core. Only the package name in its header comment differs. Below
  the marker each plugin supplies `nextSteps()`, `leftovers()` and
  `keptFiles()`.
- `test/install-suite.sh` and `test/package-suite.sh`: the same checks, adapted
  per plugin. A change to the installer core usually needs a matching test
  change in each.
- `.claude/skills/release/SKILL.md`: the same flow, with real per-repo
  differences (whether `main` has CI, the CHANGELOG heading style).

With the [`plugins/` links](#working-on-the-plugins) in place, both of these
should print nothing:

```bash
cmp plugins/claude-notify-resume/.github/workflows/publish.yml \
    plugins/claude-video-digest/.github/workflows/publish.yml
diff <(sed -n '/^.use strict/,/── This plugin/p' plugins/claude-notify-resume/bin/claude-notify-resume.js) \
     <(sed -n '/^.use strict/,/── This plugin/p' plugins/claude-video-digest/bin/claude-video-digest.js)
```

## Working on the plugins

For changes that span several plugins, `plugins/` holds symlinks to the plugin
repos cloned next to this one. They are local only (gitignored), so recreate
them on a fresh checkout:

```bash
mkdir -p plugins
ln -s ../../claude-notify-resume plugins/claude-notify-resume
ln -s ../../claude-video-digest plugins/claude-video-digest
```

Each link is its own git repository: commit and push inside it, not here.

## Never rename this marketplace, or move this repo

The marketplace's `name` (`anaidenko`) is the install coordinate every user has
on disk, and marketplaces are keyed by that name rather than by repo URL — two
manifests sharing a name silently fight over one slot, and the loser's plugins
stay `enabled` while failing to load, with their hooks quietly dead. That is why
these plugins live in one shared marketplace instead of each declaring their
own.

The repository's address is fixed for a second reason: every published version
of the `npx` installers has `anaidenko` and `anaidenko/claude-plugins` built in,
and an npm version cannot be changed once released. After a move, an older
installer would either add the old address, which works only while GitHub's
redirect lasts, or find the marketplace at its new address, take it for someone
else's, and refuse to run.
