# snapdiff

A tiny CLI that fetches a URL, diffs it against the last snapshot, and describes
the delta.

- **One integration:** an outbound HTTP fetch. Nothing else.
- **Stdlib only:** Python 3.9+, zero third-party dependencies.
- Snapshots are stored as plain files on disk (default `.snapshots/`).

## Usage

```bash
# First run saves a baseline
python -m snapdiff https://example.com

# Run again later to see what changed since the baseline
python -m snapdiff https://example.com

# See the full unified diff
python -m snapdiff https://example.com --show-diff

# Check without updating the baseline
python -m snapdiff https://example.com --no-save

# Store snapshots somewhere else
python -m snapdiff https://example.com --dir /path/to/snapshots

# Exit non-zero when the page changed (handy for cron/CI monitoring)
python -m snapdiff https://example.com --fail-on-change
```

### JS-rendered pages (optional)

Some pages ship almost no HTML and paint their content with JavaScript. For those,
`--render` re-fetches the page with a headless browser:

```bash
python -m snapdiff https://example.com --render
```

It only kicks in when the plain fetch looks empty or effectively text-less, so the
normal stdlib fetch path is unchanged for everything else. Rendering needs the
optional Playwright extra, installed in two steps:

```bash
pip install -r requirements-render.txt
playwright install chromium
```

If Playwright (or its browser) is missing, `--render` fails with a clear message
telling you which step to run.

### Exit codes

| Code | Meaning |
| ---- | ------- |
| `0`  | Success — no change, or `--fail-on-change` not set |
| `1`  | Fetch failed |
| `2`  | A change was detected (only with `--fail-on-change`; the first-run baseline never counts as a change) |

Example output on a change:

```
Change detected at https://example.com:
  +2 line(s) added
    + New announcement banner
  -1 line(s) removed
    - Old promo text
```

## How it works

```
fetch (urllib)  ->  diff (difflib)  ->  describe  ->  save baseline (files)
```

- `snapdiff/fetch.py` — the only network code.
- `snapdiff/render.py` — optional headless-browser fallback (`--render`); the only
  browser code, with Playwright imported lazily.
- `snapdiff/store.py` — read/write snapshots on disk.
- `snapdiff/diff.py` — compute and describe the delta (pure functions).
- `snapdiff/cli.py` — wires it together.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests never touch the network.

## Working with Claude Code

Project context lives in `CLAUDE.md`, and four sub-agents live in
`.claude/agents/` (`planner`, `code-writer`, `tester`, `reviewer`). Use them
instead of ad-hoc prompts — a typical flow is planner → code-writer → tester →
reviewer.
