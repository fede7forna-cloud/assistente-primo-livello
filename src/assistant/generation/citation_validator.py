"""Gate 2: turn what the model claimed into what we are willing to show.

The first gate, in ``retrieval/retriever.py``, keeps the model away from
questions the documentation does not cover. This one catches what that gate
cannot see: a model given perfectly relevant context that invents a source
anyway — a section id that reads plausibly and does not exist.

The two are redundant on purpose. The first saves a call, the second saves the
answer.

This module is also the reason ``Answer``'s ``ValueError`` is unreachable. That
exception marks a defect in our code, never a path a user can trigger, and a
draft claiming ``answer_found`` while citing an unretrieved section is ordinary
traffic. Every such draft is *degraded* here, never constructed and left to
explode: every ``Answer`` in this file is built through a named constructor whose
preconditions have already been checked.

No dependency on anything outside the domain: a draft and a context in, an
``Answer`` out. It can be exercised without a model, a network or a database.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from assistant.domain.models import (
    Answer,
    AnswerDraft,
    Citation,
    Chunk,
    CitationRef,
    Outcome,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)

ESCALATION_MESSAGE = (
    "Non ho trovato questa informazione nella documentazione, quindi preferisco "
    "non risponderti a memoria. Ti conviene contattare l'assistenza, che può "
    "verificare il caso specifico."
)
"""Handover to a human operator.

Public on purpose. The first gate escalates too, from ``service.py``, and it has
to say the same thing: two wordings for the same situation would drift apart and
the user would learn to read them as two different problems.
"""

CLARIFICATION_MESSAGE = (
    "La domanda può riferirsi a più procedure diverse e non vorrei indicarti "
    "quella sbagliata. Puoi precisare meglio cosa stai cercando di fare?"
)
"""Fallback when the model asks for clarification without saying what is unclear."""


def validate_answer(draft: AnswerDraft, context: Sequence[RetrievedChunk]) -> Answer:
    """Validate an untrusted draft against the chunks actually retrieved.

    Returns an ``Answer`` in every case. There is no failure mode that reaches
    the caller as an exception: an unusable draft becomes an escalation, which is
    a legitimate outcome rather than an error.
    """
    if draft.outcome is Outcome.AMBIGUOUS_QUESTION:
        return Answer.ambiguous(draft.message.strip() or CLARIFICATION_MESSAGE)

    if draft.outcome is not Outcome.ANSWER_FOUND:
        return _escalate(draft.message)

    steps = tuple(step.strip() for step in draft.steps if step.strip())
    if not steps:
        logger.warning(
            "Risposta scartata: esito %s senza passaggi utilizzabili",
            draft.outcome,
        )
        return _escalate(draft.message)

    citations = _resolve_citations(draft.citations, context)
    if citations is None:
        return _escalate(draft.message)

    return Answer.found(steps=steps, citations=citations, message=draft.message.strip())


def _escalate(model_message: str) -> Answer:
    """Hand over to a human, preferring the model's wording when it gave one.

    The fallback is not decoration: ``Answer`` requires a non-empty message for
    every outcome other than ``ANSWER_FOUND``, so a model that escalates without
    explaining itself would otherwise trip the invariant.
    """
    return Answer.not_in_documentation(model_message.strip() or ESCALATION_MESSAGE)


def _resolve_citations(
    claimed: Sequence[CitationRef],
    context: Sequence[RetrievedChunk],
) -> tuple[Citation, ...] | None:
    """Resolve claimed sources against retrieved chunks, or ``None`` if any fails.

    **One unverifiable citation invalidates the whole answer.** Keeping the valid
    citations and dropping the invented one is tempting and wrong: the steps are
    a single block of prose, and there is no way to tell which of them came from
    the section that does not exist. The result would be a partly invented
    procedure presented as documented — and the surviving citation would make it
    look checked.
    """
    if not claimed:
        logger.warning("Risposta scartata: esito answer_found senza citazioni")
        return None

    available = {_reference_of(chunk): chunk for chunk in _chunks(context)}

    resolved: dict[str, Citation] = {}
    for reference in claimed:
        key = _normalise(reference)
        chunk = available.get(key)
        if chunk is None:
            logger.warning(
                "Risposta scartata: il modello cita '%s', che non è tra le sezioni "
                "recuperate (%s)",
                reference.reference,
                ", ".join(sorted(available)) or "nessuna",
            )
            return None
        # Titles come from the retrieved chunk, never from what the model wrote:
        # the label shown to the user has to match the section it points at.
        resolved.setdefault(key, Citation.from_chunk(chunk))

    return tuple(resolved.values())


def _chunks(context: Sequence[RetrievedChunk]) -> tuple[Chunk, ...]:
    return tuple(retrieved.chunk for retrieved in context)


def _reference_of(chunk: Chunk) -> str:
    return _key(chunk.doc_id, chunk.anchor)


def _normalise(reference: CitationRef) -> str:
    """Reduce a claimed reference to the form used for comparison.

    A citation can fail to match for two very different reasons: formatting noise
    — stray spaces, capitals, a leading ``#``, the whole ``doc_id#anchor`` pasted
    into the ``doc_id`` field — or invention. Treating the first as the second
    escalates questions we could have answered, one ticket per stray character.

    So the *format* is recovered here, and only the format. Anything that still
    fails to match afterwards is an invented source, and the caller drops the
    answer.
    """
    doc_id = reference.doc_id.strip()
    anchor = reference.anchor.strip().lstrip("#").strip()

    # "contratti-noleggio#cauzione" written into doc_id, with anchor left empty
    # or repeated: the model rendered the reference instead of splitting it.
    if "#" in doc_id:
        doc_id, _, embedded = doc_id.partition("#")
        anchor = anchor or embedded.strip()

    return _key(doc_id, anchor)


def _key(doc_id: str, anchor: str) -> str:
    return f"{doc_id.strip().casefold()}#{anchor.strip().casefold()}"
