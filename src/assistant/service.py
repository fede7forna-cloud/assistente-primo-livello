"""The one place that decides the order of operations.

Retrieval, generation and validation each know how to do their job and none of
them knows when it is their turn. This module says: gate, model, gate — and it is
the only module that says it. The CLI and the API are thin shells over the same
object, so a question asked from a terminal and the same question asked over HTTP
cannot take different paths through the system.

The two gates are redundant on purpose. The first spares a call to the model when
the documentation has nothing to offer; the second catches a model that invents a
source despite being handed relevant context. Neither is trusted alone.
"""

from __future__ import annotations

import logging

from assistant.domain.models import Answer, Outcome
from assistant.domain.ports import LLMClient, VectorStore
from assistant.generation.citation_validator import ESCALATION_MESSAGE, validate_answer
from assistant.retrieval.retriever import Retriever

logger = logging.getLogger(__name__)


class AssistantService:
    """Answers a question using only the indexed documentation.

    ``llm_client`` is typed on the port rather than on the OpenRouter adapter, so
    the whole flow can be exercised with a double and no network. ``retriever``
    is one of our own classes, not a port: choosing what counts as relevant is
    domain logic, not an external dependency.
    """

    def __init__(
        self,
        retriever: Retriever,
        llm_client: LLMClient,
        store: VectorStore,
    ) -> None:
        self._retriever = retriever
        self._llm_client = llm_client
        self._store = store

    def index_size(self) -> int:
        """How many chunks are indexed, for health checks and CLI output.

        Whether the deployment is usable is an application-level question, and
        this class is the application: the CLI and the API ask it here rather
        than each reaching for a vector store of its own. ``store`` is the very
        object the retriever already searches, wired once in the factory.

        Raises:
            Exception: whatever the store raises. A failing index is a broken
                installation, not an empty one, and the two must not be
                indistinguishable to whoever is monitoring.
        """
        return self._store.count()

    def ask(self, question: str) -> Answer:
        """Answer ``question``, or hand it over to a human.

        Returns a valid ``Answer`` in every case the documentation can speak to —
        including "it does not cover this", which is an outcome and not a failure.

        **Infrastructure failures are not outcomes and are not converted into
        one.** ``LLMError``, ``EmbeddingError`` and ``VectorStoreError`` travel
        straight through this method to the caller, carrying the Italian message
        their adapter wrote for the user.

        The reason is that ``Outcome`` describes the documentation, while an
        exception describes the system. ``NOT_IN_DOCUMENTATION`` asserts "I
        looked, and it is not there". If the provider was unreachable, nothing
        was looked at: returning that outcome would state something false about
        the corpus, send the user to open a ticket instead of retrying, and
        inflate the escalation rate — the one metric that tells us where the
        documentation actually has holes — with numbers that no later analysis
        can separate out.

        Raises:
            ValueError: if ``question`` is blank. Validating user input belongs
                to the CLI and the API schemas.
            Exception: whatever the retrieval or generation adapters raise,
                unwrapped. Their messages are written to be shown as they are.
        """
        text = question.strip()
        if not text:
            raise ValueError("question must not be blank")

        # Gate 1. An empty result means the documentation has nothing similar
        # enough, and the model is never called: no cost, and nothing to
        # hallucinate from.
        context = self._retriever.retrieve(text)
        if not context:
            return _escalated(Answer.not_in_documentation(ESCALATION_MESSAGE))

        draft = self._llm_client.generate_answer(text, context)

        # Gate 2, against the very same context the model was given. Rebuilding
        # or reordering it here would verify the citations against a different
        # set than the one the model saw, and the check would stop meaning
        # anything.
        return _logged(validate_answer(draft, context))


def _escalated(answer: Answer) -> Answer:
    logger.info("Cancello 1: nessuna sezione pertinente, richiesta inoltrata a un umano")
    return answer


def _logged(answer: Answer) -> Answer:
    """Record what was answered and from where.

    The question itself is deliberately not logged: it may carry the user's own
    data, and it explains nothing that the outcome and the cited references do
    not already explain.
    """
    if answer.outcome is Outcome.ANSWER_FOUND:
        logger.info(
            "Risposta trovata: %d passaggi, fonti %s",
            len(answer.steps),
            ", ".join(citation.reference for citation in answer.citations),
        )
    else:
        logger.info("Esito %s", answer.outcome)
    return answer
