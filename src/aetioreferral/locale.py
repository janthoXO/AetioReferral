import tomllib
from functools import cache
from pathlib import Path
from typing import Any

LOCALES_DIR = Path(__file__).parent / "locales"


def supported_languages() -> list[str]:
    return sorted(p.stem for p in LOCALES_DIR.glob("*.toml"))


def resolve_language(tag: str) -> str:
    """Exact locale file first (`de-CH`), then the base language (`de`)."""
    supported = {s.lower(): s for s in supported_languages()}
    for candidate in (tag.lower(), tag.lower().split("-")[0]):
        if candidate in supported:
            return supported[candidate]
    raise ValueError(f"unsupported language {tag!r}, supported: {', '.join(supported.values())}")


@cache
def load_locale(tag: str) -> dict[str, Any]:
    return tomllib.loads((LOCALES_DIR / f"{resolve_language(tag)}.toml").read_text(encoding="utf-8"))
