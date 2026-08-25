# Claude Plugins by Andrii Naidenko

A [Claude Code](https://docs.claude.com/en/docs/claude-code) plugin
marketplace. One `marketplace add`, then install whichever plugins you want.

```bash
claude plugin marketplace add anaidenko/claude-plugins
claude plugin install claude-notify-resume@anaidenko
claude plugin install claude-video-digest@anaidenko
```

Restart Claude Code afterwards — plugin and hook config is read at startup.

## Plugins

### [claude-notify-resume](https://github.com/anaidenko/claude-notify-resume)

Desktop notifications that name the conversation they came from — and reopen
it when clicked. Each banner is titled with the chat's own name, so parallel
sessions stay distinguishable. macOS and Linux.

### [claude-video-digest](https://github.com/anaidenko/claude-video-digest)

Turns any video into a readable digest — timestamped contact sheet,
frame-grouped transcript, and no hallucinated captions on silent tracks.

## Updating

```bash
claude plugin marketplace update anaidenko
claude plugin update claude-notify-resume@anaidenko
```

Updating one plugin does not touch the others — they are versioned and
installed independently.

## Uninstalling

```bash
claude plugin uninstall claude-notify-resume@anaidenko
```

## Notes

This repository holds only the marketplace manifest — each plugin lives in its
own repository and is referenced by URL, so plugins release on their own
schedule. Adding a plugin here does not affect installs of the others.

## License

MIT

## Maintaining this marketplace

The manifest is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).
Validate any edit before pushing — a broken manifest breaks `plugin install`
for everyone, and nothing here runs locally:

```bash
python3 scripts/validate-marketplace.py --network
```

**Adding a plugin** — append an entry with `name`, `description`, and a
`source` pointing at its repository:

```json
{
    "name": "my-plugin",
    "source": { "source": "url", "url": "https://github.com/anaidenko/my-plugin.git" },
    "description": "One line, shown in the plugin browser."
}
```

The `name` is the install coordinate (`my-plugin@anaidenko`) and must match the
plugin's own `.claude-plugin/plugin.json`.

**Releasing a new version of a plugin** — nothing to do here. Plugin versions
are read from each plugin repo's `plugin.json` at install time, so a release is
just a push in that repo. This manifest deliberately carries no `version`
fields; adding one would mean keeping it in sync on every release.

**Renaming or moving a plugin repo** — update its `url` here in the same pass,
otherwise installs keep resolving to the old location until GitHub's redirect
lapses.

**Changing a plugin's description** — the copy here is what the plugin browser
shows; the plugin's own README is separate. Update both, or they drift.

**Never rename this marketplace.** Its `name` (`anaidenko`) is the install
coordinate every user has on disk, and marketplaces are keyed by that name
rather than by repo URL — two manifests sharing a name silently fight over one
slot, and the loser's plugins stay `enabled` while failing to load, with their
hooks quietly dead. That is why these plugins live in one shared marketplace
instead of each declaring their own.
