"""Gate 1: decide whether the documentation has anything to say at all.

This is the first of the two redundant gates described in CLAUDE.md, and the
cheaper one. It runs before the language model is involved: if the best chunk
retrieved for a question is not similar enough, the request is escalated to a
human without a single token being generated. No cost, and no opportunity to
hallucinate — the model never sees the question.

The second gate lives in ``generation/citation_validator.py`` and catches what
this one cannot: a model that invents a plausible source *despite* being given
relevant context.

Deliberately not here:

* the escalation message. This module decides *whether* the documentation
  covers a question, not what to tell the user — that is the service's call,
  and the wording belongs with the other user-facing Italian strings;
* ``Outcome``. Returning an empty result keeps this a retrieval concern.
  Mapping "nothing relevant" onto ``Outcome.NOT_IN_DOCUMENTATION`` is a
  decision about the answer, and the answer is assembled elsewhere.

The threshold is calibrated for one specific embedding model. Both values come
from ``Settings`` and neither may be hardcoded here; see the calibration note in
``config/settings.yaml`` before changing either.
"""

from __future__ import annotations

import logging

from assistant.domain.models import RetrievedChunk
from assistant.domain.ports import Embedder, VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Finds the documentation chunks that are relevant to a question.

    Holds the two ports rather than concrete adapters, so the tests exercise the
    gate with fakes and never load a model or touch a database.
    """

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        top_k: int,
        similarity_threshold: float,
    ) -> None:
        if top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {top_k}")
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], got {similarity_threshold}"
            )
        self._embedder = embedder
        self._store = store
        self._top_k = top_k
        self._similarity_threshold = similarity_threshold

    def retrieve(self, question: str) -> tuple[RetrievedChunk, ...]:
        """Return the chunks that may be used to answer ``question``.

        An **empty result means the gate is closed**: the documentation does not
        cover the question and the caller must escalate rather than ask the model
        anyway. It is not an error and not an empty answer.

        When the gate opens, the chunks below the threshold are still dropped.
        ``top_k`` is an upper bound on how much context may be handed over, not a
        quota to fill: passing along the tail of barely-related sections would
        widen the surface the model is free to cite without making the answer
        better.

        Raises:
            ValueError: if ``question`` is blank. Validating user input is the
                job of the CLI and the API schemas; reaching this point with an
                empty question is a defect upstream, not a user mistake.
        """
        text = question.strip()
        if not text:
            raise ValueError("question must not be blank")

        vector = self._embedder.embed_query(text)
        candidates = tuple(self._store.search(vector, self._top_k))
        if not candidates:
            logger.info(
                "Nessun chunk recuperato: indice vuoto o nessun risultato per la domanda"
            )
            return ()

        # max() rather than candidates[0]: the port guarantees the results are
        # sorted, but the gate is too important to depend on an adapter honouring it.
        best = max(candidate.score for candidate in candidates)
        if best < self._similarity_threshold:
            logger.info(
                "Cancello 1 chiuso: punteggio migliore %.4f sotto la soglia %.4f "
                "(%d candidati) — nessuna chiamata al modello",
                best,
                self._similarity_threshold,
                len(candidates),
            )
            return ()

        relevant = tuple(
            candidate
            for candidate in candidates
            if candidate.score >= self._similarity_threshold
        )
        logger.debug(
            "Cancello 1 aperto: %d chunk su %d sopra la soglia %.4f, migliore %.4f (%s)",
            len(relevant),
            len(candidates),
            self._similarity_threshold,
            best,
            ", ".join(candidate.reference for candidate in relevant),
        )
        return relevant
