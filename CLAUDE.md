# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

AetioReferral renders synthetic medical referral letters (German Überweisungsbrief baseline) as PDF, exposed as an MCP server and a CLI. `README.md` is the user overview, `README-DEV.md` the full technical reference; the design decisions and roadmap live in GitHub issue #22.

## Commands

```bash
uv sync                                              # install (Python 3.13, deps from uv.lock)
uv run pytest                                        # all tests
uv run pytest tests/test_service.py::test_same_seed_same_letter   # one test
uv run ruff format && uv run ruff check              # format + lint (line length 140)
uv run pyright                                       # type check; covers src/ only
uv run aetioreferral render examples/letter.json -o letter.pdf --seed 7
uv run aetioreferral mcp [--http]                    # MCP server, stdio or streamable HTTP on 127.0.0.1:8000/mcp
docker build -t aetioreferral .                      # distroless runtime image
```

CI (`.github/workflows/build.yml`) runs `uv sync --locked`, `ruff format --check`, `ruff check`, `pyright`, `pytest`, a CLI render and `uv build`; keep all of them green.

## Architecture

Ports and adapters with one deep core module:

- `service.py` is the whole core interface: `render_letter(spec, seed)` and `generate_letter(description, drafter, language, seed)`. Both CLI (`cli.py`) and MCP (`mcp_server.py`) are thin driving adapters over these two functions.
- The only port is `Drafter` (`drafter.py`): `PydanticAIDrafter` in production, a fake in tests. It exists only when `LLM_PROVIDER` and `LLM_MODEL` are set (env or `.env` in the working directory, see `config.py`); otherwise the `generate` CLI subcommand and the `generate_referral_letter` MCP tool are not registered at all. That is why `cli.py` has two root command classes (`App`, `AppWithGenerate`).
- Render flow: `identities.fill(spec, seed)` fills every missing patient/sender/recipient field with seeded Faker (given fields always win, `patient: null` means no patient block) → `render.view(letter)` turns the complete letter plus locale into ready-made strings → `typst.compile` with that JSON in `sys_inputs`. Faker and Typst are internal, not ports; tests run real Typst.
- `template/letter.typ` contains no words and never evaluates data strings (caller text must not become Typst markup). Every word the service adds comes from `locales/<lang>.toml`.
- `LetterSpec` (`letter.py`) is the input contract and, via its `Field(description=...)`s, the MCP tool schema LLM clients see. All sections are plain text.

## Making changes

- New letter section: add the field to `LetterSpec`, its name to `SECTION_FIELDS` in `render.py` (this sets the print order), and a label to **every** locale file. A test enforces that all locale files have the same keys as `de.toml`.
- New language: copy `locales/de.toml` to `<tag>.toml`; no code change. Region tags fall back to the base language.
- Use `Field(default=...)` (keyword), not `Field(None, ...)`; pyright does not see positional defaults on pydantic models.
- The MCP SDK is 2.x: `mcp.server.mcpserver.MCPServer` (FastMCP was renamed), types from `mcp_types`, test clients via `mcp.Client(server)`.
- `pydantic_ai.BANNER_ENABLED = False` in `drafter.py` must stay: the first-run banner would corrupt the MCP stdio stream.
- Tests `chdir` into a temp dir and clear `LLM_*` so a developer's `.env` cannot leak in; keep new tests independent of the working directory.
- Mark deliberate shortcuts with a `ponytail:` comment naming the limit and the upgrade path (see `identities.py`).

## Build and release

- `Dockerfile`: build stage `debian:trixie-slim` with Debian's Python 3.13, runtime `gcr.io/distroless/python3-debian13:nonroot`. Both must keep the same interpreter path (`/usr/bin/python3.13`) or the copied venv breaks.
- `release.yml` publishes on every push to `main` that touches `src/`, `pyproject.toml`, `uv.lock`, the `Dockerfile` or the workflow: patch-bumped GitHub release plus `ghcr.io/janthoxo/aetioreferral/server`. Merging such a PR releases.
- `astral-sh/setup-uv` has no moving major tags; pin an exact version (e.g. `@v10.2.0`).

## Repo conventions

- `docs/` is local-only (excluded via `.git/info/exclude`) and holds the design doc; never commit it.
- AetioMed (`../AetioMed`) is the sister project that embeds these letters; its integration contract is in `README-DEV.md#aetiomed-integration`.
