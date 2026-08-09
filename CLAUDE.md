# CLAUDE.md

Project context for Claude Code. Read this before doing anything in this repo.

## What snapdiff is

A tiny CLI that watches a web page for changes:

1. **Fetch** a URL over HTTP(S).
2. **Diff** the freshly fetched content against the last saved snapshot of that URL.
3. **Describe** the delta in a human-readable summary, then save the new snapshot as the baseline.

That is the whole product. Do not expand scope without being asked.

## Hard constraints

- **The only way content enters the tool is by fetching the target URL.** No
  databases, no message queues, no third-party content APIs, no cloud SDKs. The
  raw fetch is plain HTTP(S).
- **Standard library only for the core.** The default path (fetch → diff →
  describe → save) has zero third-party runtime dependencies. If you think you
  need a dependency in the core, you are probably overcomplicating it — stop and
  reconsider.
- **One sanctioned exception: an optional headless-render mode.** Some pages are
  JS-rendered and return an empty/shell body over plain HTTP. An *opt-in*
  `--render` fallback may drive a headless browser (Playwright) to obtain the
  rendered DOM. This is the ONLY permitted third-party dependency, it is
  **optional** (imported lazily, only when render mode is used), and it is still
  just fetching the same target URL — not a second integration. The tool must
  install, import, run, and pass its tests with Playwright absent.
- **Keep the stack simple.** Python 3.9+, stdlib. Tests use `unittest` (stdlib)
  and never touch the network or launch a browser.
- Snapshots are stored on the local filesystem. No network storage.

## Stack

- Language: Python 3 (3.9+), standard library only for the core.
- HTTP: `urllib.request`.
- Optional render mode: `playwright` (lazy import, only for `--render`).
- Diffing: `difflib`.
- Storage: local files under a snapshot directory (default `.snapshots/`), one
  entry per URL keyed by a hash of the URL.
- Tests: `unittest`, run with `python -m unittest discover`.
- CLI entry point: `python -m snapdiff <url>`.

## Layout

```
snapdiff/
  __init__.py     # version + public exports
  fetch.py        # plain HTTP fetch (stdlib urllib)
  render.py       # OPTIONAL headless-browser fetch (lazy Playwright import)
  htmltext.py     # reduce HTML to visible text (stdlib html.parser)
  store.py        # read/write snapshots on disk
  diff.py         # compute + describe the delta between two snapshots
  cli.py          # argument parsing + orchestration
tests/            # unittest tests, no network access, no browser launch
```

## Working agreements

- Networking lives only in `fetch.py` (plain HTTP) and `render.py` (optional
  headless browser). Nothing else in the package opens a socket or launches a
  browser. This keeps everything else trivially unit-testable without a network.
- The `playwright` import in `render.py` must be lazy (inside the function), so
  importing the package and running the test suite never require it to be present.
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
