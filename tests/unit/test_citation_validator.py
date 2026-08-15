"""Gate 2: the promise that an invented source cannot reach a user.

The last test in this file is the important one. ``Answer`` raises ``ValueError``
on an inconsistent construction, and ``domain/models.py`` states that the
exception marks a defect in our code and must never be reachable from user
traffic. A draft claiming ``answer_found`` while citing a section that was never
retrieved is ordinary traffic, so the only thing standing between the two is
``validate_answer``. That property is asserted by exhaustion rather than by
example.
"""

from __future__ import annotations

import itertools

import pytest

from assistant.domain.models import Answer, AnswerDraft, CitationRef, Outcome
from assistant.generation.citation_validator import (
    CLARIFICATION_MESSAGE,
    ESCALATION_MESSAGE,
    validate_answer,
)
from tests.conftest import make_draft, make_retrieved

CONTEXT = (
    make_retrieved(doc_id="guida-esempio", anchor="primo-accesso", section_title="Primo accesso"),
    make_retrieved(
        doc_id="procedure-esempio",
        anchor="archiviare-scheda",
        doc_title="Procedure di esempio",
        section_title="Archiviare una scheda",
    ),
)


def test_verified_citation_is_resolved_from_the_retrieved_chunk() -> None:
    answer = validate_answer(make_draft(), CONTEXT)

    assert answer.outcome is Outcome.ANSWER_FOUND
    citation = answer.citations[0]
    # Titles come from the chunk, never from the model: CitationRef cannot even
    # carry them, so the label shown to a user cannot disagree with the section.
    assert citation.doc_title == "Guida di esempio"
    assert citation.section_title == "Primo accesso"
    assert citation.reference == "guida-esempio#primo-accesso"


def test_one_invented_citation_discards_the_whole_answer() -> None:
    """No partial salvage. This is the case gate 2 exists for.

    Keeping the valid citation and dropping the invented one would present a
    partly invented procedure as documented, with the surviving citation making
    it look checked. The steps are one block of prose: there is no way to know
    which of them came from the section that does not exist.
    """
    draft = make_draft(
        steps=("Aprire la sezione.", "Premere Conferma."),
        citations=(("guida-esempio", "primo-accesso"), ("guida-esempio", "sezione-inventata")),
    )

    answer = validate_answer(draft, CONTEXT)

    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION
    assert answer.steps == ()
    assert answer.citations == ()


@pytest.mark.parametrize(
    ("label", "doc_id", "anchor"),
    [
        ("ancora con cancelletto", "guida-esempio", "#primo-accesso"),
        ("maiuscole", "GUIDA-ESEMPIO", "PRIMO-ACCESSO"),
        ("spazi", "  guida-esempio  ", "  primo-accesso  "),
        ("riferimento intero nel doc_id", "guida-esempio#primo-accesso", ""),
        ("riferimento intero più ancora", "guida-esempio#primo-accesso", "primo-accesso"),
    ],
)
def test_formatting_noise_is_recovered_not_rejected(label: str, doc_id: str, anchor: str) -> None:
    """Format is recovered, content never is.

    A citation can fail to match because the model mangled the format or because
    it invented the source. Treating the first as the second escalates questions
    we could have answered — one ticket per stray character.
    """
    draft = make_draft(citations=((doc_id, anchor),))

    answer = validate_answer(draft, CONTEXT)

    assert answer.outcome is Outcome.ANSWER_FOUND, label
    assert answer.citations[0].reference == "guida-esempio#primo-accesso"


def test_duplicate_citations_are_deduplicated_in_order() -> None:
    draft = make_draft(
        citations=(
            ("procedure-esempio", "archiviare-scheda"),
            ("guida-esempio", "primo-accesso"),
            ("procedure-esempio", "archiviare-scheda"),
        )
    )

    answer = validate_answer(draft, CONTEXT)

    assert [citation.reference for citation in answer.citations] == [
        "procedure-esempio#archiviare-scheda",
        "guida-esempio#primo-accesso",
    ]


@pytest.mark.parametrize(
    ("label", "draft"),
    [
        ("nessuna citazione", make_draft(citations=())),
        ("nessun passaggio", make_draft(steps=())),
        ("passaggi vuoti", make_draft(steps=("", "   "))),
        ("tutte inventate", make_draft(citations=(("manuale-fantasma", "sezione-x"),))),
    ],
)
def test_unusable_answers_are_degraded(label: str, draft: AnswerDraft) -> None:
    answer = validate_answer(draft, CONTEXT)

    assert answer.outcome is Outcome.NOT_IN_DOCUMENTATION, label
    assert answer.steps == ()
    assert answer.citations == ()


def test_answer_found_against_empty_context_is_degraded() -> None:
    assert validate_answer(make_draft(), ()).outcome is Outcome.NOT_IN_DOCUMENTATION


@pytest.mark.parametrize("outcome", [Outcome.NOT_IN_DOCUMENTATION, Outcome.AMBIGUOUS_QUESTION])
def test_non_found_outcomes_drop_steps_and_citations(outcome: Outcome) -> None:
    """``Answer`` forbids these fields on a non-found outcome; the model sends them anyway."""
    draft = make_draft(outcome=outcome, message="testo del modello")

    answer = validate_answer(draft, CONTEXT)

    assert answer.outcome is outcome
    assert answer.steps == ()
    assert answer.citations == ()
    assert answer.message == "testo del modello"


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (Outcome.NOT_IN_DOCUMENTATION, ESCALATION_MESSAGE),
        (Outcome.AMBIGUOUS_QUESTION, CLARIFICATION_MESSAGE),
    ],
)
def test_blank_message_falls_back(outcome: Outcome, expected: str) -> None:
    """Without a fallback, an empty message would trip ``Answer``'s invariant."""
    answer = validate_answer(AnswerDraft(outcome=outcome, message="   "), CONTEXT)

    assert answer.message == expected


def test_answer_value_error_is_unreachable() -> None:
    """Exhaustive: no combination of draft and context can raise from the validator.

    This is the permanent form of the property ``domain/models.py`` states in
    prose. It is asserted over the product of every shape a draft can take,
    because a single well-chosen example would not survive the next change to the
    validator.
    """
    outcomes = list(Outcome)
    step_sets = [(), ("",), ("   ", ""), ("Aprire.", "Salvare."), ("solo uno",)]
    citation_sets = [
        (),
        (CitationRef(doc_id="guida-esempio", anchor="primo-accesso"),),
        (CitationRef(doc_id="inesistente", anchor="inesistente"),),
        (
            CitationRef(doc_id="guida-esempio", anchor="primo-accesso"),
            CitationRef(doc_id="inesistente", anchor="inesistente"),
        ),
        (CitationRef(doc_id="", anchor=""),),
        (CitationRef(doc_id="#", anchor="#"),),
        (CitationRef(doc_id="guida-esempio#primo-accesso", anchor=""),),
    ]
    messages = ["", "   ", "testo del modello"]
    contexts = [CONTEXT, (), CONTEXT[:1]]

    checked = 0
    for outcome, steps, citations, message, context in itertools.product(
        outcomes, step_sets, citation_sets, messages, contexts
    ):
        draft = AnswerDraft(
            outcome=outcome, steps=steps, citations=citations, message=message
        )

        answer = validate_answer(draft, context)

        checked += 1
        assert isinstance(answer, Answer)
        if answer.outcome is Outcome.ANSWER_FOUND:
            assert answer.steps and all(step.strip() for step in answer.steps)
            available = {retrieved.reference for retrieved in context}
            assert all(citation.reference in available for citation in answer.citations)
            assert len({citation.reference for citation in answer.citations}) == len(
                answer.citations
            )
        else:
            assert answer.steps == ()
            assert answer.citations == ()
            assert answer.message.strip()

    assert checked > 900, "la combinatoria si è ristretta: la proprietà non è più esaustiva"
