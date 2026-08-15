"""HTTP request and response bodies. Distinct from the domain models on purpose.

The domain describes what the system is; these describe what travels over the
wire. Keeping them apart is what allows either to change without dragging the
other along — a field renamed in a payload is a breaking change for clients, a
field renamed in the domain is a refactor.

The one type shared with the domain is ``Outcome``: it is not a model but the
contract itself, and reusing it puts the three values into the OpenAPI schema
where clients can see them instead of guessing from prose.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from assistant.domain.models import Answer, Citation, Outcome


class ChatRequest(BaseModel):
    """A question for the assistant."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="La domanda dell'utente, in linguaggio naturale.",
        examples=["Come esporto un report in CSV?"],
    )


class CitationSchema(BaseModel):
    """A verified source, with everything needed to render a link to it.

    ``doc_id`` and ``anchor`` are always present, so a client can build its own
    address even when the server has no idea where the documentation is
    published. ``url`` is filled in only when it can be filled in truthfully.
    """

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(description="Identificatore del documento.")
    anchor: str = Field(description="Ancora della sezione all'interno del documento.")
    doc_title: str = Field(description="Titolo leggibile del documento.")
    section_title: str = Field(description="Titolo leggibile della sezione citata.")
    reference: str = Field(
        description="Riferimento citabile, nella forma doc_id#ancora.",
        examples=["report-esportazioni#esportare-csv"],
    )
    url: str | None = Field(
        default=None,
        description=(
            "Indirizzo pubblico della sezione. Vale null quando la documentazione "
            "non è pubblicata da nessuna parte (documentation.url_template non "
            "configurato): in quel caso il collegamento va costruito dal client a "
            "partire da doc_id e anchor."
        ),
    )

    @classmethod
    def from_domain(cls, citation: Citation, url_template: str | None) -> Self:
        return cls(
            doc_id=citation.doc_id,
            anchor=citation.anchor,
            doc_title=citation.doc_title,
            section_title=citation.section_title,
            reference=citation.reference,
            url=_format_url(url_template, citation),
        )


class ChatResponse(BaseModel):
    """The assistant's answer, whatever it turned out to be.

    All three outcomes are returned with status 200, escalation included: "the
    documentation does not cover this" is a correct answer to a question, not a
    failure of the service. Only infrastructure faults produce an error status.
    """

    model_config = ConfigDict(extra="forbid")

    outcome: Outcome = Field(
        description=(
            "answer_found: passaggi e citazioni presenti. "
            "not_in_documentation: rinvio all'assistenza umana. "
            "ambiguous_question: serve un chiarimento."
        )
    )
    message: str = Field(
        default="",
        description=(
            "Testo per l'utente. Obbligatorio per not_in_documentation e "
            "ambiguous_question, spesso vuoto per answer_found."
        ),
    )
    steps: list[str] = Field(
        default_factory=list,
        description=(
            "Passaggi operativi in ordine, non numerati: l'ordine dell'array è la "
            "numerazione, e spetta al client renderla. Possono contenere Markdown "
            "inline (**grassetto**) per i nomi di pulsanti e campi, ripreso dalla "
            "documentazione. Vuoto se l'esito non è answer_found."
        ),
    )
    citations: list[CitationSchema] = Field(
        default_factory=list,
        description=(
            "Sezioni effettivamente usate, già verificate contro i blocchi "
            "recuperati. Vuoto se l'esito non è answer_found."
        ),
    )

    @classmethod
    def from_domain(cls, answer: Answer, url_template: str | None) -> Self:
        return cls(
            outcome=answer.outcome,
            message=answer.message,
            steps=list(answer.steps),
            citations=[
                CitationSchema.from_domain(citation, url_template)
                for citation in answer.citations
            ],
        )


class HealthResponse(BaseModel):
    """Whether this deployment can actually answer anything."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        description=(
            "'ok' quando l'indice contiene almeno un blocco, 'degraded' quando è "
            "vuoto — nel qual caso la risposta ha stato 503."
        )
    )
    indexed_chunks: int = Field(description="Blocchi di documentazione indicizzati.")
    model: str = Field(description="Modello di linguaggio configurato.")
    embedding_model: str = Field(description="Modello di embedding configurato.")


def _format_url(url_template: str | None, citation: Citation) -> str | None:
    if url_template is None:
        return None
    return url_template.format(doc_id=citation.doc_id, anchor=citation.anchor)
