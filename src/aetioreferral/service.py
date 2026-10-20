from aetioreferral.drafter import Drafter
from aetioreferral.identities import fill, new_seed
from aetioreferral.letter import LetterSpec, RenderedLetter
from aetioreferral.locale import resolve_language
from aetioreferral.render import render_pdf


async def render_letter(spec: LetterSpec, *, seed: int | None = None) -> RenderedLetter:
    """Fill every missing identity field, then render the PDF. Same spec and seed give the same letter."""
    seed = new_seed() if seed is None else seed
    letter = fill(spec, seed)
    return RenderedLetter(pdf=await render_pdf(letter), letter=letter, seed=seed)


async def generate_letter(description: str, drafter: Drafter, *, language: str | None = None, seed: int | None = None) -> RenderedLetter:
    """Let the drafter write the letter content from free text, then render it. `language=None`: the description's language."""
    if language is not None:
        resolve_language(language)
    return await render_letter(await drafter.draft(description, language), seed=seed)
