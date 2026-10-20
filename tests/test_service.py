import base64
import datetime
import io
import tomllib

import pytest
from mcp import Client
from pypdf import PdfReader

from aetioreferral import cli
from aetioreferral.config import load_llm_settings
from aetioreferral.letter import LetterSpec
from aetioreferral.locale import LOCALES_DIR, resolve_language
from aetioreferral.mcp_server import build_server
from aetioreferral.service import generate_letter, render_letter

pytestmark = pytest.mark.anyio

SPEC = {
    "recipient_specialty": "Gastroenterologie",
    "reason": "Bitte um Ösophagogastroduodenoskopie.",
    "history": "Seit zwei Monaten Oberbauchbeschwerden.",
    "medication": "Ramipril 5 mg 1-0-0\nIbuprofen 600 mg bei Bedarf",
    "patient": {"name": "Anna Schmidt", "sex": "f"},
    "date": "2026-10-20",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def no_llm_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # keep a developer's .env out of the tests
    for var in ("LLM_PROVIDER", "LLM_MODEL", "LLM_URL", "LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    cli.drafter.cache_clear()


def pdf_text(pdf: bytes) -> str:
    return " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)


class FakeDrafter:
    async def draft(self, description: str, language: str | None) -> LetterSpec:
        return LetterSpec(recipient_specialty="Kardiologie", reason=description, language=language or "de")


async def test_render_prints_given_sections_and_fills_identities():
    rendered = await render_letter(LetterSpec.model_validate(SPEC), seed=1)
    text = pdf_text(rendered.pdf)
    for expected in ("Gastroenterologie", "Ösophagogastroduodenoskopie", "Ramipril 5 mg", "Anna Schmidt", rendered.letter.sender.name):
        assert expected in text
    assert "Allergien" not in text and "Verdachtsdiagnose" not in text  # empty sections leave no heading
    assert rendered.letter.patient.name == "Anna Schmidt"  # given field wins
    assert rendered.letter.patient.birth_date and rendered.letter.sender.identifiers.keys() == {"BSNR", "LANR"}


async def test_same_seed_same_letter():
    spec = LetterSpec.model_validate(SPEC)
    first, second = await render_letter(spec, seed=42), await render_letter(spec, seed=42)
    assert first.letter == second.letter
    assert first.seed == 42


async def test_age_gives_matching_birth_date():
    spec = LetterSpec.model_validate(SPEC | {"patient": {"age": 54}})
    birth = (await render_letter(spec, seed=3)).letter.patient.birth_date
    date = datetime.date(2026, 10, 20)
    assert date.year - birth.year - ((date.month, date.day) < (birth.month, birth.day)) == 54


async def test_patient_null_leaves_out_patient_block():
    rendered = await render_letter(LetterSpec.model_validate(SPEC | {"patient": None}), seed=1)
    text = pdf_text(rendered.pdf)
    assert rendered.letter.patient is None
    assert "geb." not in text and "hiermit überweisen wir" in text


def test_patient_three_states():
    base = {"recipient_specialty": "x", "reason": "y"}
    assert LetterSpec.model_validate(base).patient is not None
    assert LetterSpec.model_validate(base | {"patient": {}}).patient is not None
    assert LetterSpec.model_validate(base | {"patient": None}).patient is None


def test_locale_files_complete_and_lookup():
    def keys(data, prefix=""):
        return {f"{prefix}{k}" for k, v in data.items()} | {
            key for k, v in data.items() if isinstance(v, dict) for key in keys(v, f"{prefix}{k}.")
        }

    reference = keys(tomllib.loads((LOCALES_DIR / "de.toml").read_text()))
    for path in LOCALES_DIR.glob("*.toml"):
        assert keys(tomllib.loads(path.read_text())) == reference, path.name
    assert resolve_language("de-AT") == "de"
    with pytest.raises(ValueError, match="de"):
        resolve_language("xx")


def test_llm_settings_states(monkeypatch):
    assert load_llm_settings() is None
    monkeypatch.setenv("LLM_MODEL", "some-model")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        load_llm_settings()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert load_llm_settings().model == "some-model"


def test_llm_settings_from_dotenv(tmp_path):
    (tmp_path / ".env").write_text("LLM_PROVIDER=anthropic\nLLM_MODEL=claude-test\nLLM_API_KEY=sk-test\nOTHER=x\n")
    settings = load_llm_settings()
    assert settings and settings.provider == "anthropic" and settings.api_key and settings.api_key.get_secret_value() == "sk-test"


async def test_generate_letter_with_fake_drafter():
    rendered = await generate_letter("Abklärung Belastungsdyspnoe", FakeDrafter(), seed=1)
    assert "Belastungsdyspnoe" in pdf_text(rendered.pdf)


async def test_mcp_render_tool_returns_pdf_and_filled_letter():
    async with Client(build_server(None)) as client:
        assert [t.name for t in (await client.list_tools()).tools] == ["render_referral_letter"]
        result = await client.call_tool("render_referral_letter", {"letter": SPEC | {"patient": {}}, "seed": 5})
    assert not result.is_error
    assert base64.b64decode(result.content[0].resource.blob).startswith(b"%PDF")
    assert result.structured_content["letter"]["patient"]["name"]
    assert result.structured_content["seed"] == 5


async def test_mcp_generate_tool_only_with_drafter():
    async with Client(build_server(FakeDrafter())) as client:
        assert "generate_referral_letter" in [t.name for t in (await client.list_tools()).tools]


def test_cli_generate_only_with_llm_config(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "generate" not in capsys.readouterr().out
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    cli.drafter.cache_clear()
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "generate" in capsys.readouterr().out
