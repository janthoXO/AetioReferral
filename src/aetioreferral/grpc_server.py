from typing import Any

import grpc
from google.protobuf import json_format
from pydantic import ValidationError

from aetioreferral.drafter import Drafter
from aetioreferral.letter import LetterSpec, RenderedLetter
from aetioreferral.service import generate_letter, render_letter
from aetioreferral.v1 import referral_pb2_grpc
from aetioreferral.v1.referral_pb2 import GenerateLetterRequest, Letter, RenderLetterRequest
from aetioreferral.v1.referral_pb2 import RenderedLetter as RenderedLetterMsg

SEX_TO_PROTO = {"f": "SEX_FEMALE", "m": "SEX_MALE", "d": "SEX_DIVERSE"}
SEX_FROM_PROTO = {v: k for k, v in SEX_TO_PROTO.items()}


def letter_from_proto(msg: Letter) -> LetterSpec:
    data = json_format.MessageToDict(msg, preserving_proto_field_name=True)
    if data.pop("no_patient", False):
        data["patient"] = None
    elif "patient" in data:
        data["patient"]["sex"] = SEX_FROM_PROTO.get(data["patient"].get("sex", ""))  # SEX_UNSPECIFIED is omitted
    return LetterSpec.model_validate(data)  # uint32 `age` arrives as a number, not a string (only 64-bit ints are strings)


def letter_to_proto(letter: LetterSpec) -> Letter:
    data = _drop_none(letter.model_dump(mode="json"))
    if "patient" in data:
        if "sex" in data["patient"]:
            data["patient"]["sex"] = SEX_TO_PROTO[data["patient"]["sex"]]
    else:
        data["no_patient"] = True
    return json_format.ParseDict(data, Letter())


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    return value


class _Servicer(referral_pb2_grpc.ReferralServiceServicer):
    def __init__(self, drafter: Drafter | None):
        self.drafter = drafter

    async def RenderLetter(self, request: RenderLetterRequest, context: grpc.aio.ServicerContext) -> RenderedLetterMsg:
        try:
            seed = request.seed if request.HasField("seed") else None
            return _reply(await render_letter(letter_from_proto(request.letter), seed=seed))
        except (ValidationError, ValueError) as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

    async def GenerateLetter(self, request: GenerateLetterRequest, context: grpc.aio.ServicerContext) -> RenderedLetterMsg:
        if self.drafter is None:
            await context.abort(grpc.StatusCode.UNIMPLEMENTED, "no LLM configured (set LLM_PROVIDER and LLM_MODEL)")
        try:
            language = request.language if request.HasField("language") else None
            seed = request.seed if request.HasField("seed") else None
            return _reply(await generate_letter(request.description, self.drafter, language=language, seed=seed))
        except (ValidationError, ValueError) as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))


def _reply(rendered: RenderedLetter) -> RenderedLetterMsg:
    return RenderedLetterMsg(pdf=rendered.pdf, letter=letter_to_proto(rendered.letter), seed=rendered.seed)


def build_server(drafter: Drafter | None) -> grpc.aio.Server:
    """aetioreferral.v1.ReferralService, plaintext. Add a port, then start() inside a running loop."""
    # ponytail: no TLS, health or reflection service; add grpcio-health-checking when an orchestrator probes it.
    server = grpc.aio.server()
    referral_pb2_grpc.add_ReferralServiceServicer_to_server(_Servicer(drafter), server)
    return server
