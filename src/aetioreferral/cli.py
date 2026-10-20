import sys
from functools import cache, partial
from pathlib import Path
from typing import Any, cast

import anyio
from pydantic import AliasChoices, BaseModel, Field, ValidationError
from pydantic_ai.exceptions import UnexpectedModelBehavior, UserError
from pydantic_settings import CliApp, CliPositionalArg, CliSettingsSource, CliSubCommand

from aetioreferral.config import load_llm_settings
from aetioreferral.drafter import Drafter, PydanticAIDrafter
from aetioreferral.letter import LetterSpec, RenderedLetter
from aetioreferral.mcp_server import build_server
from aetioreferral.service import generate_letter, render_letter


@cache
def drafter() -> Drafter | None:
    settings = load_llm_settings()
    return PydanticAIDrafter(settings) if settings else None


def _write(rendered: RenderedLetter, output: Path) -> None:
    output.write_bytes(rendered.pdf)
    print(f"wrote {output} (seed {rendered.seed})", file=sys.stderr)


class Render(BaseModel):
    """Render a letter from a LetterSpec JSON file."""

    file: CliPositionalArg[str] = Field(description="LetterSpec JSON file, '-' reads stdin")
    output: Path = Field(validation_alias=AliasChoices("o", "output"), description="PDF file to write")
    seed: int | None = Field(default=None, description="Reproduce an earlier letter")

    def cli_cmd(self) -> None:
        text = sys.stdin.read() if self.file == "-" else Path(self.file).read_text(encoding="utf-8")
        _write(anyio.run(partial(render_letter, LetterSpec.model_validate_json(text), seed=self.seed)), self.output)


class Generate(BaseModel):
    """Write and render a letter from a free-text description (needs LLM_* configuration)."""

    description: CliPositionalArg[str]
    output: Path = Field(validation_alias=AliasChoices("o", "output"), description="PDF file to write")
    language: str | None = Field(default=None, description="BCP 47 tag; default: the description's language")
    seed: int | None = Field(default=None, description="Seed for the generated identities")

    def cli_cmd(self) -> None:
        d = drafter()
        assert d is not None
        _write(anyio.run(partial(generate_letter, self.description, d, language=self.language, seed=self.seed)), self.output)


class Mcp(BaseModel):
    """Run the MCP server (stdio by default)."""

    http: bool = Field(default=False, description="Serve streamable HTTP instead of stdio")
    host: str = "127.0.0.1"
    port: int = 8000

    def cli_cmd(self) -> None:
        server = build_server(drafter())
        if self.http:
            server.run("streamable-http", host=self.host, port=self.port)
        else:
            server.run()


class App(BaseModel):
    """Synthetic medical referral letters as PDF."""

    render: CliSubCommand[Render]
    mcp: CliSubCommand[Mcp]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


class AppWithGenerate(App):
    generate: CliSubCommand[Generate]


def main(argv: list[str] | None = None) -> None:
    try:
        app = AppWithGenerate if drafter() else App
        # CliSettingsSource is typed for BaseSettings; plain BaseModel roots work at runtime.
        source = CliSettingsSource(
            cast(Any, app), cli_prog_name="aetioreferral", cli_kebab_case=True, cli_implicit_flags=True, cli_hide_none_type=True
        )
        CliApp.run(app, cli_args=argv, cli_settings_source=source)
    except (ValidationError, ValueError, OSError, UnexpectedModelBehavior, UserError) as e:
        sys.exit(f"error: {e}")
