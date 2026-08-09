# CLAUDE.md

Project context for Claude Code. Read this before doing anything in this repo.

## What snapdiff is

A tiny CLI that watches a web page for changes:

1. **Fetch** a URL over HTTP(S).
2. **Diff** the freshly fetched content against the last saved snapshot of that URL.
3. **Describe** the delta in a human-readable summary, then save the new snapshot as the baseline.

That is the whole product. Do not expand scope without being asked.

## Hard constraints

- **The only external integration is an outbound HTTP fetch.** No databases, no
  message queues, no third-party APIs, no cloud SDKs, no headless browsers.
- **Standard library only.** Zero third-party runtime dependencies. If you think
  you need a dependency, you are probably overcomplicating it — stop and reconsider.
- **Keep the stack simple.** Python 3.9+, stdlib. Tests use `unittest` (stdlib).
- Snapshots are stored on the local filesystem. No network storage.

## Stack

- Language: Python 3 (3.9+), standard library only.
- HTTP: `urllib.request`.
- Diffing: `difflib`.
- Storage: local files under a snapshot directory (default `.snapshots/`), one
  entry per URL keyed by a hash of the URL.
- Tests: `unittest`, run with `python -m unittest discover`.
- CLI entry point: `python -m snapdiff <url>`.

## Layout

```
snapdiff/
  __init__.py     # version + public exports
  fetch.py        # HTTP fetch (the ONLY network code)
  store.py        # read/write snapshots on disk
  diff.py         # compute + describe the delta between two snapshots
  cli.py          # argument parsing + orchestration
tests/            # unittest tests, no network access
```

## Working agreements

- Networking lives only in `fetch.py`. Nothing else in the package opens a socket.
  This keeps everything else trivially unit-testable without hitting the network.
- Pure functions where possible: `diff.py` and `store.py` take data in and give
  data out. Side effects (disk, network, stdout) stay at the edges (`cli.py`).
- Every behavior change ships with a test. Tests must never touch the network.
- Keep functions short and readable. Match the surrounding style.

## Commands

```bash
# Run the tool
python -m snapdiff https://example.com

# Run tests
python -m unittest discover -s tests -v
```

## Roles (sub-agents)

Four project sub-agents live in `.claude/agents/`. Use them instead of writing
ad-hoc prompts:

- **planner** — turns a request into a concrete, minimal step-by-step plan.
- **code-writer** — implements a plan with small, clean stdlib-only changes.
- **tester** — writes/runs `unittest` tests and reports failures.
- **reviewer** — read-only review for scope creep, bugs, and simplicity.

A typical flow: `planner` → `code-writer` → `tester` → `reviewer`.
