from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Sex(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SEX_UNSPECIFIED: _ClassVar[Sex]
    SEX_FEMALE: _ClassVar[Sex]
    SEX_MALE: _ClassVar[Sex]
    SEX_DIVERSE: _ClassVar[Sex]
SEX_UNSPECIFIED: Sex
SEX_FEMALE: Sex
SEX_MALE: Sex
SEX_DIVERSE: Sex

class RenderLetterRequest(_message.Message):
    __slots__ = ("letter", "seed")
    LETTER_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    letter: Letter
    seed: int
    def __init__(self, letter: _Optional[_Union[Letter, _Mapping]] = ..., seed: _Optional[int] = ...) -> None: ...

class GenerateLetterRequest(_message.Message):
    __slots__ = ("description", "language", "seed")
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    description: str
    language: str
    seed: int
    def __init__(self, description: _Optional[str] = ..., language: _Optional[str] = ..., seed: _Optional[int] = ...) -> None: ...

class RenderedLetter(_message.Message):
    __slots__ = ("pdf", "letter", "seed")
    PDF_FIELD_NUMBER: _ClassVar[int]
    LETTER_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    pdf: bytes
    letter: Letter
    seed: int
    def __init__(self, pdf: _Optional[bytes] = ..., letter: _Optional[_Union[Letter, _Mapping]] = ..., seed: _Optional[int] = ...) -> None: ...

class Letter(_message.Message):
    __slots__ = ("language", "recipient_specialty", "reason", "request", "urgent", "suspected_diagnosis", "diagnoses", "history", "findings", "prior_treatment", "medication", "allergies", "extra_sections", "attachments", "patient", "no_patient", "sender", "recipient", "date")
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_SPECIALTY_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    URGENT_FIELD_NUMBER: _ClassVar[int]
    SUSPECTED_DIAGNOSIS_FIELD_NUMBER: _ClassVar[int]
    DIAGNOSES_FIELD_NUMBER: _ClassVar[int]
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    FINDINGS_FIELD_NUMBER: _ClassVar[int]
    PRIOR_TREATMENT_FIELD_NUMBER: _ClassVar[int]
    MEDICATION_FIELD_NUMBER: _ClassVar[int]
    ALLERGIES_FIELD_NUMBER: _ClassVar[int]
    EXTRA_SECTIONS_FIELD_NUMBER: _ClassVar[int]
    ATTACHMENTS_FIELD_NUMBER: _ClassVar[int]
    PATIENT_FIELD_NUMBER: _ClassVar[int]
    NO_PATIENT_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    language: str
    recipient_specialty: str
    reason: str
    request: str
    urgent: bool
    suspected_diagnosis: str
    diagnoses: str
    history: str
    findings: str
    prior_treatment: str
    medication: str
    allergies: str
    extra_sections: _containers.RepeatedCompositeFieldContainer[Section]
    attachments: _containers.RepeatedScalarFieldContainer[str]
    patient: Patient
    no_patient: bool
    sender: Doctor
    recipient: Doctor
    date: str
    def __init__(self, language: _Optional[str] = ..., recipient_specialty: _Optional[str] = ..., reason: _Optional[str] = ..., request: _Optional[str] = ..., urgent: _Optional[bool] = ..., suspected_diagnosis: _Optional[str] = ..., diagnoses: _Optional[str] = ..., history: _Optional[str] = ..., findings: _Optional[str] = ..., prior_treatment: _Optional[str] = ..., medication: _Optional[str] = ..., allergies: _Optional[str] = ..., extra_sections: _Optional[_Iterable[_Union[Section, _Mapping]]] = ..., attachments: _Optional[_Iterable[str]] = ..., patient: _Optional[_Union[Patient, _Mapping]] = ..., no_patient: _Optional[bool] = ..., sender: _Optional[_Union[Doctor, _Mapping]] = ..., recipient: _Optional[_Union[Doctor, _Mapping]] = ..., date: _Optional[str] = ...) -> None: ...

class Section(_message.Message):
    __slots__ = ("heading", "text")
    HEADING_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    heading: str
    text: str
    def __init__(self, heading: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class Patient(_message.Message):
    __slots__ = ("sex", "name", "birth_date", "age", "address", "insurer", "insurance_number")
    SEX_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BIRTH_DATE_FIELD_NUMBER: _ClassVar[int]
    AGE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    INSURER_FIELD_NUMBER: _ClassVar[int]
    INSURANCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    sex: Sex
    name: str
    birth_date: str
    age: int
    address: str
    insurer: str
    insurance_number: str
    def __init__(self, sex: _Optional[_Union[Sex, str]] = ..., name: _Optional[str] = ..., birth_date: _Optional[str] = ..., age: _Optional[int] = ..., address: _Optional[str] = ..., insurer: _Optional[str] = ..., insurance_number: _Optional[str] = ...) -> None: ...

class Doctor(_message.Message):
    __slots__ = ("name", "title", "specialty", "practice", "address", "phone", "fax", "identifiers")
    class IdentifiersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    SPECIALTY_FIELD_NUMBER: _ClassVar[int]
    PRACTICE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    FAX_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    title: str
    specialty: str
    practice: str
    address: str
    phone: str
    fax: str
    identifiers: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., title: _Optional[str] = ..., specialty: _Optional[str] = ..., practice: _Optional[str] = ..., address: _Optional[str] = ..., phone: _Optional[str] = ..., fax: _Optional[str] = ..., identifiers: _Optional[_Mapping[str, str]] = ...) -> None: ...
