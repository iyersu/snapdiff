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
```

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
