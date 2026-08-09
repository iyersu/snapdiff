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

### Selecting an element (`--select`)

Often you only care about one part of a page — a price, a status badge, a stock
count — and want the surrounding markup churn to stay out of the diff. `--select`
reduces the fetched (or rendered) HTML to the visible text of the elements that
match a small CSS-selector subset, before diffing:

```bash
# Watch just the price element
python -m snapdiff https://shop.example/product --select 'span.price'
```

Supported selectors (one compound selector only):

- a tag name — `span`
- one or more classes — `.price`, `.badge.sale`
- an id — `#total`
- compounds of the above — `span.price`, `div#cart.summary`

Explicitly out of scope (rejected with a non-zero exit): descendant/child
combinators (`div span`, `div > span`), sibling combinators (`~`, `+`),
attribute selectors (`[data-x]`), pseudo-classes (`:first-child`), selector
lists (`a, b`), and the universal selector (`*`).

Both an unsupported selector and a selector that matches no elements exit
non-zero (code `1`), so a broken or stale selector fails loudly instead of
silently diffing nothing.

Because `--select` already reduces to visible text, `--text` is redundant when
you use it. `--select` combines naturally with `--render` and `--fail-on-change`
for price monitoring of JS-heavy pages:

```bash
python -m snapdiff --render --select 'span.money' --fail-on-change https://shop.example/product
```

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
- `snapdiff/select.py` — reduce HTML to matching elements' text (`--select`);
  a tiny CSS-selector subset, pure stdlib.
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
