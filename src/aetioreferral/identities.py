import datetime
import random

from faker import Faker

from aetioreferral.letter import DoctorIn, LetterSpec, PatientIn
from aetioreferral.locale import load_locale


def fill(spec: LetterSpec, seed: int) -> LetterSpec:
    """Return `spec` with every missing identity field generated. Given fields always win; same seed and spec give the same people."""
    loc = load_locale(spec.language)
    fake = Faker(loc["faker_locale"])
    fake.seed_instance(seed)
    date = spec.date or datetime.date.today()
    sender = _doctor(spec.sender, fake, loc, loc["default_sender_specialty"])
    recipient = _doctor(spec.recipient, fake, loc, spec.recipient_specialty)
    patient = None if spec.patient is None else _patient(spec.patient, fake, loc, date)
    return spec.model_copy(update={"date": date, "sender": sender, "recipient": recipient, "patient": patient})


def _doctor(d: DoctorIn, fake: Faker, loc: dict, default_specialty: str) -> DoctorIn:
    name = d.name or f"{fake.first_name()} {fake.last_name()}"
    title = d.title if d.title is not None else fake.random_element(loc["doctor_titles"])
    full_name = f"{title} {name}".strip()
    # ponytail: random 9-digit identifiers without check digits; valid LANR/BSNR is future work (#2).
    identifiers = {k: fake.numerify("#########") for k in loc["identifier_keys"]} | d.identifiers
    return DoctorIn(
        name=name,
        title=title,
        specialty=d.specialty or default_specialty,
        practice=d.practice or loc["phrases"]["practice"].format(doctor=full_name),
        address=d.address or fake.address(),
        phone=d.phone or fake.phone_number(),
        fax=d.fax or fake.phone_number(),
        identifiers=identifiers,
    )


def _patient(p: PatientIn, fake: Faker, loc: dict, date: datetime.date) -> PatientIn:
    sex = p.sex or fake.random_element(("f", "m"))
    first = {"f": fake.first_name_female, "m": fake.first_name_male}.get(sex, fake.first_name)
    birth_date = p.birth_date
    if birth_date is None:
        age = p.age if p.age is not None else fake.random_int(18, 90)
        # Any day that makes the patient exactly `age` on the letter date.
        birth_date = _years_before(date, age) - datetime.timedelta(days=fake.random_int(0, 364))
    return PatientIn(
        sex=sex,
        name=p.name or f"{first()} {fake.last_name()}",
        birth_date=birth_date,
        age=p.age,
        address=p.address or fake.address(),
        insurer=p.insurer or (fake.random_element(loc["insurers"]) if loc["insurers"] else None),
        insurance_number=p.insurance_number or fake.bothify(loc["insurance_number_format"], letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    )


def _years_before(date: datetime.date, years: int) -> datetime.date:
    try:
        return date.replace(year=date.year - years)
    except ValueError:  # 29 February
        return date.replace(year=date.year - years, day=28)


def new_seed() -> int:
    return random.randrange(2**31)
