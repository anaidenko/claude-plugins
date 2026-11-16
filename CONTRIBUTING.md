# Maintaining the marketplace

This repository holds only the marketplace manifest,
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Each
plugin lives in its own repository and is referenced by URL, so plugins release
on their own schedule, and adding a plugin here does not affect installs of the
others.

## Validating

Validate any edit before pushing — a broken manifest breaks `plugin install`
for everyone, and nothing here runs locally:

```bash
python3 scripts/validate-marketplace.py --network
```

CI runs the same check on every push, and weekly: a referenced repo can be
renamed or made private without a commit landing here.

## Adding a plugin

Append an entry with `name`, `description`, and a `source` pointing at its
repository:

```json
{
    "name": "my-plugin",
    "source": { "source": "url", "url": "https://github.com/anaidenko/my-plugin.git" },
    "description": "One line, shown in the plugin browser."
}
```

The `name` is the install coordinate (`my-plugin@anaidenko`) and must match the
plugin's own `.claude-plugin/plugin.json`. Add it to the list in the README
too.

The plugin repo also takes the shared installer and release pipeline (see
[Shared across the plugin repos](#shared-across-the-plugin-repos)), and its
first npm publish is made by hand before CI can take over: the release skill's
*First publish* walks through it.

## Releasing a plugin

Nothing to do here. Each plugin repo releases with its own `/release` skill: a
version tag runs that repo's `publish.yml`, which publishes the npm installer
and then creates the GitHub Release. This manifest deliberately carries no
`version` fields; versions are read from each plugin's `plugin.json` at install
time.

Mind what reaches users when: the marketplace serves the plugin repo's default
branch, not its tags. So push the release commit and its tag together
(`git push --follow-tags`). The commit alone is a release that npm and GitHub
do not know about yet, and the tag alone (`git push --tags`) publishes to npm
while marketplace users stay on the old version.

## Renaming or moving a plugin repo

Update its `url` here in the same pass, otherwise installs keep resolving to the
old location until GitHub's redirect lapses. Update its npm trusted publisher
too, which names the repository, or the next release fails to publish. Also
update `homepage` in its `package.json`, which the installer prints.

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
