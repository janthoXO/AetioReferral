import base64

from mcp.server.mcpserver import MCPServer
from mcp_types import BlobResourceContents, CallToolResult, EmbeddedResource

from aetioreferral.drafter import Drafter
from aetioreferral.letter import LetterSpec, RenderedLetter
from aetioreferral.service import generate_letter, render_letter

RENDER_DESCRIPTION = """\
Render a referral letter from a referring doctor to a specialist as a PDF.
Write the letter content like a real referral letter: every section is plain text in the letter language, and empty sections are left out.
Leave patient, sender and recipient fields empty to have them generated; set patient to null for a letter without patient details.
Salutation, opening sentence, closing, signature and stamp are added automatically.
Returns the PDF as an embedded resource and the completed letter (with generated fields) plus the seed as structured content."""

GENERATE_DESCRIPTION = """\
Write and render a realistic referral letter from a free-text description, e.g. who refers whom with which complaints.
The letter follows the description where it asks for something specific, otherwise it mirrors a real referral letter.
language: BCP 47 tag of the letter; omit to use the description's language.
Returns the same result as render_referral_letter."""


def build_server(drafter: Drafter | None) -> MCPServer:
    """The generate tool exists only when an LLM is configured."""
    server = MCPServer("aetioreferral", instructions="Generates synthetic medical referral letters as PDF.")

    @server.tool(description=RENDER_DESCRIPTION)
    async def render_referral_letter(letter: LetterSpec, seed: int | None = None) -> CallToolResult:
        return _result(await render_letter(letter, seed=seed))

    if drafter is not None:

        @server.tool(description=GENERATE_DESCRIPTION)
        async def generate_referral_letter(description: str, language: str | None = None, seed: int | None = None) -> CallToolResult:
            return _result(await generate_letter(description, drafter, language=language, seed=seed))

    return server


def _result(rendered: RenderedLetter) -> CallToolResult:
    pdf = BlobResourceContents(
        uri=f"letter://{rendered.seed}.pdf", mime_type="application/pdf", blob=base64.b64encode(rendered.pdf).decode()
    )
    return CallToolResult(
        content=[EmbeddedResource(resource=pdf)],
        structured_content={"letter": rendered.letter.model_dump(mode="json"), "seed": rendered.seed},
    )
