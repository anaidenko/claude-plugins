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
