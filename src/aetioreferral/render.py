import json
from pathlib import Path
from typing import Any

import anyio.to_thread
import typst

from aetioreferral.letter import DoctorIn, LetterSpec
from aetioreferral.locale import load_locale

TEMPLATE_DIR = Path(__file__).parent / "template"

# Section fields in letter order; each heading comes from the locale's [labels].
SECTION_FIELDS = ("suspected_diagnosis", "diagnoses", "reason", "history", "findings", "prior_treatment", "medication", "allergies")


async def render_pdf(letter: LetterSpec) -> bytes:
    """`letter` must be complete (see identities.fill). Compiles off the event loop."""
    data = json.dumps(view(letter), ensure_ascii=False)
    return await anyio.to_thread.run_sync(
        lambda: bytes(
            typst.compile(
                TEMPLATE_DIR / "letter.typ",
                font_paths=[TEMPLATE_DIR / "fonts"],
                ignore_system_fonts=True,
                sys_inputs={"data": data},
            )
        )
    )


def view(letter: LetterSpec) -> dict[str, Any]:
    """Everything the template prints, as ready-made strings. The template holds no words and no logic beyond layout."""
    loc = load_locale(letter.language)
    labels, phrases = loc["labels"], loc["phrases"]
    assert letter.date is not None
    request = letter.request or phrases["default_request"]

    patient = None
    if letter.patient is not None:
        p = letter.patient
        assert p.sex and p.birth_date
        title = loc["patient_title"][p.sex]
        line = f"{title} {p.name}".strip() + f", {labels['born']} {p.birth_date.strftime(loc['date_format'])}"
        details = [
            (p.address or "").replace("\n", ", "),
            p.insurer or "",
            f"{labels['insurance_number']} {p.insurance_number}" if p.insurance_number else "",
        ]
        patient = {"line": line, "details": " · ".join(d for d in details if d)}
        intro = phrases["intro"].format(patient=loc["patient_noun"][p.sex], request=request)
    else:
        intro = phrases["intro_without_patient"].format(request=request)

    sections = [{"heading": labels[f], "text": text} for f in SECTION_FIELDS if (text := getattr(letter, f))]
    sections += [s.model_dump() for s in letter.extra_sections]

    return {
        "lang": letter.language.split("-")[0].lower(),  # hyphenation and typographic rules
        "sender": _doctor(letter.sender, labels, loc["identifier_keys"]),
        "recipient": _doctor(letter.recipient, labels, []),
        "date": letter.date.strftime(loc["date_format"]),
        "patient": patient,
        "referral": f"{labels['referral_to']}: {letter.recipient_specialty}",
        "urgent": labels["urgent"] if letter.urgent else None,
        "salutation": phrases["salutation"],
        "intro": intro,
        "sections": sections,
        "closing": phrases["closing"],
        "attachments": {"heading": labels["attachments"], "items": letter.attachments} if letter.attachments else None,
    }


def _doctor(d: DoctorIn, labels: dict[str, str], identifier_keys: list[str]) -> dict[str, Any]:
    contact = [f"{labels['phone']} {d.phone}" if d.phone else "", f"{labels['fax']} {d.fax}" if d.fax else ""]
    return {
        "name": f"{d.title} {d.name}".strip(),
        "signature": d.name or "",
        "specialty": d.specialty or "",
        "practice": d.practice or "",
        "address": (d.address or "").splitlines(),
        "contact": [c for c in contact if c],
        "identifiers": [f"{k} {d.identifiers[k]}" for k in identifier_keys if d.identifiers.get(k)],
    }
