import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from aetioreferral.locale import resolve_language, supported_languages

Sex = Literal["f", "m", "d"]


class Section(BaseModel):
    heading: str = Field(description="Section heading, e.g. 'Sozialanamnese' or 'Procedere'.")
    text: str = Field(description="Plain text. A blank line starts a new paragraph.")


class PatientIn(BaseModel):
    """Every field optional: given fields are kept, missing ones are generated."""

    sex: Sex | None = Field(default=None, description="'f', 'm' or 'd'. Generated if missing.")
    name: str | None = Field(default=None, description="Full name. Generated if missing.")
    birth_date: datetime.date | None = Field(default=None, description="Generated if missing, from `age` when given.")
    age: int | None = Field(
        default=None, ge=0, le=120, description="Age in years at the letter date. Used only when `birth_date` is missing."
    )
    address: str | None = Field(default=None, description="Postal address, lines separated by newlines. Generated if missing.")
    insurer: str | None = Field(default=None, description="Health insurer. Generated if missing.")
    insurance_number: str | None = Field(default=None, description="Insurance number. Generated if missing.")


class DoctorIn(BaseModel):
    """Sender or recipient. Every field optional: given fields are kept, missing ones are generated."""

    name: str | None = Field(default=None, description="Full name without title. Generated if missing.")
    title: str | None = Field(default=None, description="Academic title, e.g. 'Dr. med.'. Generated if missing; '' for none.")
    specialty: str | None = Field(
        default=None, description="Medical specialty. Defaults to general practice (sender) or `recipient_specialty` (recipient)."
    )
    practice: str | None = Field(default=None, description="Practice or clinic name. Generated if missing.")
    address: str | None = Field(default=None, description="Postal address, lines separated by newlines. Generated if missing.")
    phone: str | None = Field(default=None, description="Generated if missing.")
    fax: str | None = Field(default=None, description="Generated if missing.")
    identifiers: dict[str, str] = Field(
        default_factory=dict,
        description="Doctor and practice identifiers keyed by the locale's scheme, e.g. {'LANR': ..., 'BSNR': ...} for German. Missing keys are generated.",
    )


class LetterSpec(BaseModel):
    """One referral letter. Every section is plain text; empty sections are left out of the letter."""

    language: str = Field(
        default="de",
        description="BCP 47 language tag of the letter's labels and phrases. Caller content is never translated.",
        json_schema_extra=lambda schema: schema.update(enum=list(supported_languages())),
    )
    recipient_specialty: str = Field(description="Specialty the patient is referred to, e.g. 'Gastroenterologie'.")
    reason: str = Field(description="Fragestellung: what the referring doctor asks the specialist.")
    request: str | None = Field(
        default=None, description="Kind of referral, completing the intro sentence, e.g. 'zur Mitbehandlung'. Default from the locale."
    )
    urgent: bool = Field(default=False, description="Marks the referral as urgent.")
    suspected_diagnosis: str | None = Field(default=None, description="Verdachtsdiagnose.")
    diagnoses: str | None = Field(default=None, description="Known diagnoses and pre-existing conditions.")
    history: str | None = Field(default=None, description="Anamnese.")
    findings: str | None = Field(default=None, description="Befunde: examination and test results so far.")
    prior_treatment: str | None = Field(default=None, description="Treatment so far.")
    medication: str | None = Field(default=None, description="Current medication, one per line.")
    allergies: str | None = Field(default=None, description="Allergies and intolerances.")
    extra_sections: list[Section] = Field(default_factory=list, description="Further sections, printed after allergies.")
    attachments: list[str] = Field(default_factory=list, description="Anlagen, e.g. 'Laborbefund vom 14.10.2026'.")
    patient: PatientIn | None = Field(
        default_factory=PatientIn,
        description="Omitted or {}: generate the whole patient. Partly filled: keep given fields, generate the rest. null: letter has no patient block.",
    )
    sender: DoctorIn = Field(default_factory=DoctorIn, description="Referring doctor. Missing fields are generated.")
    recipient: DoctorIn = Field(default_factory=DoctorIn, description="Receiving doctor or practice. Missing fields are generated.")
    date: datetime.date | None = Field(default=None, description="Letter date. Today if missing.")

    @field_validator("language")
    @classmethod
    def _known_language(cls, tag: str) -> str:
        resolve_language(tag)
        return tag


class RenderedLetter(BaseModel):
    pdf: bytes
    letter: LetterSpec = Field(description="The input with every generated field filled in.")
    seed: int = Field(description="Pass back with the same input to reproduce the letter.")
