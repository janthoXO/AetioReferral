from typing import Protocol

import pydantic_ai
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.models import infer_model
from pydantic_ai.providers import infer_provider_class

from aetioreferral.config import LlmSettings
from aetioreferral.letter import LetterSpec

# The first-run banner would land in the MCP stdio stream.
pydantic_ai.BANNER_ENABLED = False

INSTRUCTIONS = """\
You write the content of a realistic referral letter from a referring doctor, usually a general practitioner, to a specialist, based on the user's description.

- Mirror a real referral letter as closely as possible. Fill the sections a real doctor would write for this case, including a suspected diagnosis when it fits, and leave the others empty.
- Add the plausible clinical detail a real referring doctor would know, consistent with the description: course of symptoms, examination findings, test results, medication with doses. Phrase the reason for referral as the question to the specialist.
- The description wins: follow it when it asks for something else, for example no suspected diagnosis, an urgent referral or a specific medication.
- Write every section as plain text in the letter language. Put one medication per line.
- Identity fields (patient, sender, recipient, date): fill only what the description states and leave the rest empty; it is generated afterwards. Always copy stated facts: a patient's age goes into patient.age and their sex into patient.sex ('f', 'm' or 'd'), a named doctor into sender or recipient. Set patient to null only when the description asks for a letter without patient details.
- Letter language: the one given before the description, otherwise the language of the description. Set `language` to its BCP 47 tag.
- Do not write a salutation, opening sentence or closing; they are added automatically.
"""


class DraftedLetter(LetterSpec):
    # Required here, so the model has to decide the language instead of inheriting the "de" default.
    language: str = Field(description="BCP 47 tag of the letter language, e.g. 'de' or 'en'.")


class Drafter(Protocol):
    async def draft(self, description: str, language: str | None) -> LetterSpec: ...


class PydanticAIDrafter:
    def __init__(self, settings: LlmSettings):
        options = {"base_url": settings.url, "api_key": settings.api_key.get_secret_value() if settings.api_key else None}
        options = {key: value for key, value in options.items() if value}
        model = infer_model(f"{settings.provider}:{settings.model}", provider_factory=lambda name: infer_provider_class(name)(**options))
        self._agent = Agent(model, output_type=DraftedLetter, instructions=INSTRUCTIONS, retries=3)

    async def draft(self, description: str, language: str | None) -> LetterSpec:
        prompt = description if language is None else f"Letter language: {language}\n\n{description}"
        spec = (await self._agent.run(prompt)).output
        return spec if language is None else spec.model_copy(update={"language": language})
