"""Adapter: sentence-transformers running locally. Satisfies ``ports.Embedder``.

Embeddings are computed on this machine, so indexing and answering cost nothing
per call and depend on no external service. The model itself is downloaded from
HuggingFace the first time it is used and then served from the local cache.

No model name, prefix or dimension is written here: every one of them arrives
through ``Settings``. Two consequences that are easy to miss:

* the asymmetric prefixes are a requirement of the model family, not decoration.
  Models such as e5 are trained with distinct ``query:`` and ``passage:``
  instructions, and dropping them degrades retrieval quietly. That is the whole
  reason ``Embedder`` has two methods instead of one;
* ``retrieval.similarity_threshold`` is calibrated against one specific model.
  Changing the model without recalibrating leaves the assistant answering from
  the wrong sections instead of escalating — see ``config/settings.yaml``.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from assistant.domain.ports import Vector

if TYPE_CHECKING:  # pragma: no cover - import cost avoided at runtime
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Lower bound on characters per token for Italian text with a multilingual
# tokenizer. Used only to warn before the model truncates a passage: counting
# real tokens would mean a second tokenisation pass on every chunk.
_MIN_CHARS_PER_TOKEN = 3


def _dimension_of(model: Any) -> object:
    """The model's vector size, across the rename in sentence-transformers 5.

    ``get_sentence_embedding_dimension`` still works but now warns; the newer
    ``get_embedding_dimension`` does not exist in older releases. Only used for a
    log line, so an unknown value is not worth an exception.
    """
    for name in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
        method = getattr(model, name, None)
        if method is not None:
            return method()
    return "?"


class EmbeddingError(RuntimeError):
    """The embedding model could not be loaded or applied.

    Message written for whoever runs the command, in Italian, like every other
    user-facing string in this project.
    """


class LocalEmbedder:
    """Embeds text with a sentence-transformers model held in this process.

    The model is loaded lazily, on first use. Constructing this adapter is
    therefore cheap and side-effect free, which matters because the first load
    may download several hundred megabytes: that has to happen while the user is
    running ``ingest``, not while the API is merely being wired together.
    """

    def __init__(
        self,
        model_name: str,
        query_prefix: str = "",
        passage_prefix: str = "",
    ) -> None:
        self._model_name = model_name
        self._query_prefix = query_prefix
        self._passage_prefix = passage_prefix
        self._model: SentenceTransformer | None = None

    def warm_up(self) -> None:
        """Load the model now instead of on the first question.

        Loading stays lazy by default so that constructing this adapter costs
        nothing — but a long-lived server must pay the download and the load at
        start-up rather than charging them to whoever asks the first question.
        A command-line run has nothing to gain from it: one command is one
        process, and the cost falls in the same place either way.
        """
        self._load_model()

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Vector]:
        """Embed chunk texts for indexing, in the order they were given."""
        if not texts:
            return ()
        self._warn_if_truncated(texts)
        prefixed = [f"{self._passage_prefix}{text}" for text in texts]
        return self._encode(prefixed)

    def embed_query(self, text: str) -> Vector:
        """Embed a user question, comparably with ``embed_documents``."""
        return self._encode([f"{self._query_prefix}{text}"])[0]

    def _encode(self, texts: list[str]) -> list[list[float]]:
        """Run the model, returning plain floats rather than a numpy array.

        The port allows an adapter to hand back numpy, but converting here keeps
        numpy out of every layer above: nothing downstream is then able to grow
        a dependency on it by accident.

        Normalisation is not optional. It is what puts cosine similarity on the
        scale the vector store and the escalation threshold both assume.
        """
        try:
            vectors = self._load_model().encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as exc:  # noqa: BLE001 - provider errors are opaque
            raise EmbeddingError(
                f"Calcolo degli embedding fallito con il modello "
                f"'{self._model_name}': {exc}"
            ) from exc
        return [[float(value) for value in vector] for vector in vectors]

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "Il pacchetto sentence-transformers non è installato.\n"
                'Installare le dipendenze del progetto con: pip install -e ".[dev]"'
            ) from exc

        logger.info(
            "Caricamento del modello di embedding '%s' "
            "(al primo utilizzo viene scaricato da HuggingFace)",
            self._model_name,
        )
        try:
            self._model = SentenceTransformer(self._model_name)
        except Exception as exc:  # noqa: BLE001 - loading failures are opaque
            raise EmbeddingError(
                f"Impossibile caricare il modello di embedding "
                f"'{self._model_name}': {exc}\n"
                "Verificare il nome in config/settings.yaml e, al primo avvio, "
                "la connessione a internet necessaria per scaricarlo."
            ) from exc

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Modello '%s' caricato: %s dimensioni, %d token massimi",
                self._model_name,
                _dimension_of(self._model),
                self._model.max_seq_length,
            )
        return self._model

    def _warn_if_truncated(self, texts: Sequence[str]) -> None:
        """Flag passages long enough to risk silent truncation by the model.

        Transformers cut at ``max_seq_length`` without raising anything, so a
        chunk that is too long loses its tail and nobody finds out. The estimate
        is deliberately crude — it only has to fire before the cut, not predict
        it — and the fix is to lower ``chunking.max_chars``.
        """
        budget = self._load_model().max_seq_length * _MIN_CHARS_PER_TOKEN
        oversized = [len(text) for text in texts if len(text) > budget]
        if not oversized:
            return
        logger.warning(
            "%d passaggi superano i ~%d caratteri gestibili da '%s' (max %d) e "
            "potrebbero essere troncati: ridurre chunking.max_chars",
            len(oversized),
            budget,
            self._model_name,
            max(oversized),
        )
