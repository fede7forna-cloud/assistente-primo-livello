"""Adapter: OpenRouter through the OpenAI SDK. Satisfies ``ports.LLMClient``.

OpenRouter speaks the OpenAI API, so one client covers any model it serves; the
model name and the endpoint arrive from ``Settings`` and appear nowhere in this
file.

Two things shape everything below.

**The model reasons.** Nemotron produces reasoning tokens before answering, and
that reasoning must reach neither the user nor the parser. Three independent
measures, because any one of them can fail: the provider is asked not to return
it, only ``message.content`` is ever read, and the parser strips ``<think>``
blocks if one shows up anyway.

**The output is a schema, not prose.** The answer is requested as strict JSON
matching the schema below. The defensive parsing that follows is not redundancy
for its own sake: a schema is a promise made by a provider, and this project's
whole point is not trusting promises about what a model returns.

What this adapter must never do is judge the answer. An ``AnswerDraft`` claiming
a citation that was never retrieved is expected, ordinary traffic — catching it
is the citation validator's job, and doing it here would put the second gate
inside the thing it is meant to check.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from typing import Any, Literal

import openai
from pydantic import BaseModel, ConfigDict, ValidationError

from assistant.domain.models import AnswerDraft, CitationRef, Outcome, RetrievedChunk
from assistant.generation.prompts import SYSTEM_PROMPT, build_user_message

logger = logging.getLogger(__name__)

_SCHEMA_NAME = "answer"

# Reasoning models sometimes emit their thinking inline despite being asked not
# to. Stripped before parsing rather than trusted to be absent.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_CODE_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class LLMError(RuntimeError):
    """The model could not be reached, or did not return a usable answer.

    Message written for whoever runs the command, in Italian, like every other
    user-facing string in this project. Callers treat this as "no answer
    available" — never as an empty answer.
    """


class _WireCitation(BaseModel):
    """One claimed source, exactly as it travels on the wire."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    anchor: str


class _WireAnswer(BaseModel):
    """The JSON contract with the model.

    Separate from ``AnswerDraft`` because this is a boundary type: it mirrors the
    wire format, absorbs whatever arrives and validates it. The domain type stays
    free of provider concerns.

    No field has a default. OpenAI's ``strict`` mode requires every property to
    be listed in ``required``, so optionality is expressed by empty arrays and an
    empty string — which is exactly what the system prompt asks for.
    """

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["answer_found", "not_in_documentation", "ambiguous_question"]
    steps: list[str]
    citations: list[_WireCitation]
    message: str


class OpenRouterClient:
    """Asks an OpenRouter-hosted model for a structured answer draft."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    def generate_answer(
        self,
        question: str,
        context: Sequence[RetrievedChunk],
    ) -> AnswerDraft:
        """Ask the model to answer ``question`` using only ``context``.

        Raises:
            LLMError: on any transport, provider or parsing failure. There is no
                degraded return value: a caller that cannot get a draft must
                escalate, not show the user half an answer.
        """
        response = self._call(build_user_message(question, context))
        draft = _to_draft(_parse(_content_of(response)))
        logger.debug(
            "Risposta del modello: outcome=%s, %d passaggi, %d citazioni",
            draft.outcome,
            len(draft.steps),
            len(draft.citations),
        )
        return draft

    def _call(self, user_message: str) -> Any:
        try:
            return self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": _SCHEMA_NAME,
                        "strict": True,
                        "schema": _WireAnswer.model_json_schema(),
                    },
                },
                extra_body={
                    # Let the model reason, but keep the reasoning out of the
                    # response instead of relying on it to stay quiet.
                    "reasoning": {"exclude": True},
                    # Without this, OpenRouter may route to a provider that
                    # ignores response_format and answers in prose.
                    "provider": {"require_parameters": True},
                },
            )
        except openai.AuthenticationError as exc:
            raise LLMError(
                "Chiave API rifiutata da OpenRouter.\n"
                "Verificare OPENROUTER_API_KEY nel file .env: la chiave si "
                "ottiene da https://openrouter.ai/keys"
            ) from exc
        except openai.RateLimitError as exc:
            raise LLMError(
                "Limite di richieste raggiunto su OpenRouter.\n"
                "Attendere qualche istante e riprovare, oppure scegliere un "
                "altro modello in config/settings.yaml."
            ) from exc
        except openai.BadRequestError as exc:
            raise LLMError(
                f"Richiesta rifiutata dal modello '{self._model}': {exc}\n"
                "Causa tipica: il modello configurato non supporta l'output "
                "strutturato (response_format). Le varianti gratuite di "
                "OpenRouter espongono spesso solo un sottoinsieme di parametri: "
                "verificare il modello indicato in config/settings.yaml."
            ) from exc
        except openai.APITimeoutError as exc:
            raise LLMError(
                "Il modello non ha risposto entro il tempo previsto.\n"
                "Aumentare llm.timeout_seconds in config/settings.yaml oppure "
                "riprovare."
            ) from exc
        except openai.APIConnectionError as exc:
            raise LLMError(
                f"Impossibile contattare OpenRouter: {exc}\n"
                "Verificare la connessione a internet e llm.base_url in "
                "config/settings.yaml."
            ) from exc
        except openai.APIStatusError as exc:
            raise LLMError(
                f"OpenRouter ha risposto con un errore ({exc.status_code}): {exc}"
            ) from exc


def _content_of(response: Any) -> str:
    """Pull the answer text out of the response, and nothing else.

    ``message.reasoning`` is never touched. If the provider returns the model's
    thinking despite being asked not to, it cannot reach the parser, because no
    line here goes looking for it.
    """
    choices = getattr(response, "choices", None)
    if not choices:
        raise LLMError("Il modello non ha restituito alcuna risposta.")

    choice = choices[0]
    if getattr(choice, "finish_reason", None) == "length":
        raise LLMError(
            "La risposta del modello è stata troncata perché ha raggiunto il "
            "limite di token.\n"
            "Aumentare llm.max_tokens in config/settings.yaml."
        )

    content = getattr(choice.message, "content", None)
    if not content or not content.strip():
        raise LLMError(
            "Il modello ha restituito una risposta vuota.\n"
            "Può succedere se il modello ha prodotto solo ragionamento: "
            "verificare che il modello in config/settings.yaml supporti "
            "l'output strutturato."
        )
    return content


def _parse(content: str) -> _WireAnswer:
    """Turn the raw content into a validated wire answer.

    Every step here exists because a specific thing has been observed to happen:
    thinking left inline, JSON wrapped in a code fence, a sentence of
    introduction before the object. None of them are accepted quietly — they are
    normalised, and anything still unparseable is an error, never a guess.
    """
    text = _THINK_BLOCK.sub("", content).strip()
    text = _CODE_FENCE.sub("", text).strip()

    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError(
            "La risposta del modello non contiene un oggetto JSON valido.\n"
            f"Risposta ricevuta: {content[:200]}"
        )

    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(
            f"La risposta del modello non è JSON valido: {exc}\n"
            f"Risposta ricevuta: {content[:200]}"
        ) from exc

    try:
        return _WireAnswer.model_validate(payload)
    except ValidationError as exc:
        raise LLMError(
            f"La risposta del modello non rispetta il formato previsto: {exc}\n"
            f"Risposta ricevuta: {content[:200]}"
        ) from exc


def _to_draft(wire: _WireAnswer) -> AnswerDraft:
    """Convert the wire answer into the domain's untrusted draft.

    Blank steps are dropped: a model that pads its list with empty strings would
    otherwise produce a numbered procedure with holes in it. Nothing else is
    corrected — judging the content is the validator's job, not this one's.
    """
    return AnswerDraft(
        outcome=Outcome(wire.outcome),
        steps=tuple(step.strip() for step in wire.steps if step.strip()),
        citations=tuple(
            CitationRef(doc_id=citation.doc_id.strip(), anchor=citation.anchor.strip())
            for citation in wire.citations
        ),
        message=wire.message.strip(),
    )
