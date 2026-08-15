"""Adapter: persistent ChromaDB. Satisfies ``ports.VectorStore``.

Chunks are stored with their vectors in a directory on disk, so the demo needs
no server and survives a restart.

The whole point of this file is the direction of the score. ChromaDB returns a
*distance* — lower means closer — while ``ports.VectorStore.search`` promises a
*similarity* in ``[0, 1]`` where higher means closer. Converting between the two
is this adapter's job, and getting it wrong is invisible: the retriever would
compare its escalation threshold against an inverted scale, answer from the
least relevant sections and escalate the answerable questions, without a single
exception being raised. Hence both the conversion and the guard below.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from assistant.domain.models import Chunk, RetrievedChunk
from assistant.domain.ports import Vector

logger = logging.getLogger(__name__)

# Cosine, explicitly. Chroma's default space is L2, whose distances do not
# convert to a similarity with the formula used in _to_similarity().
_SPACE_KEY = "hnsw:space"
_COSINE = "cosine"
_COLLECTION_METADATA = {_SPACE_KEY: _COSINE}

_METADATA_FIELDS = ("doc_id", "doc_title", "section_title", "anchor", "ordinal")


class VectorStoreError(RuntimeError):
    """The vector store is unusable or configured in a way that would mislead.

    Message written for whoever runs the command, in Italian, like every other
    user-facing string in this project.
    """


class ChromaVectorStore:
    """Stores chunks in a persistent ChromaDB collection.

    The client is created lazily so that constructing the adapter neither
    touches the filesystem nor imposes an ordering on start-up.
    """

    def __init__(self, persist_dir: Path, collection_name: str) -> None:
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client: Any = None
        self._collection: Any = None

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        """Store chunks and their vectors, replacing entries with the same id.

        Upsert rather than insert because ``chunk_id`` is stable across runs:
        re-indexing unchanged documentation overwrites in place instead of
        producing duplicates that would then compete in search results.
        """
        rows = list(vectors)
        if len(chunks) != len(rows):
            raise ValueError(
                f"chunks and vectors must have the same length: "
                f"{len(chunks)} chunks, {len(rows)} vectors"
            )
        if not chunks:
            return

        try:
            self._get_collection().upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=[list(vector) for vector in rows],
                documents=[chunk.text for chunk in chunks],
                metadatas=[_to_metadata(chunk) for chunk in chunks],
            )
        except VectorStoreError:
            # Already diagnosed precisely; re-wrapping would bury the instructions.
            raise
        except Exception as exc:  # noqa: BLE001 - store errors are opaque
            raise VectorStoreError(
                f"Scrittura nell'indice fallita ({self._persist_dir}): {exc}"
            ) from exc

    def search(self, vector: Vector, limit: int) -> tuple[RetrievedChunk, ...]:
        """Return at most ``limit`` chunks, most similar first.

        Scores are similarities in ``[0, 1]``, converted from Chroma's cosine
        distance, and the results are sorted here rather than trusted to arrive
        ordered: the contract callers rely on is stated in ``ports.py``, so it is
        enforced on the way out of the adapter.
        """
        if limit < 1:
            raise ValueError(f"limit must be at least 1, got {limit}")

        try:
            result = self._get_collection().query(
                query_embeddings=[list(vector)],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
        except VectorStoreError:
            raise
        except Exception as exc:  # noqa: BLE001 - store errors are opaque
            raise VectorStoreError(
                f"Ricerca nell'indice fallita ({self._persist_dir}): {exc}"
            ) from exc

        retrieved = [
            RetrievedChunk(chunk=chunk, score=_to_similarity(distance))
            for chunk, distance in _rows(result)
        ]
        return tuple(sorted(retrieved, key=lambda item: item.score, reverse=True))

    def clear(self) -> None:
        """Remove every stored chunk, by dropping and recreating the collection.

        Used when the documentation is replaced. A stale index keeps serving
        sections that no longer exist, and a citation pointing at one of them
        cannot be verified against anything.
        """
        try:
            self._get_client().delete_collection(self._collection_name)
        except Exception as exc:  # noqa: BLE001 - absent collection included
            logger.debug("Collection '%s' non eliminata: %s", self._collection_name, exc)
        self._collection = None
        self._get_collection()

    def count(self) -> int:
        """Number of chunks currently stored."""
        try:
            return int(self._get_collection().count())
        except VectorStoreError:
            raise
        except Exception as exc:  # noqa: BLE001 - store errors are opaque
            raise VectorStoreError(
                f"Lettura dell'indice fallita ({self._persist_dir}): {exc}"
            ) from exc

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            self._client = chromadb.PersistentClient(
                path=str(self._persist_dir),
                # Telemetry would make indexing perform network calls the README
                # promises it does not perform.
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        except Exception as exc:  # noqa: BLE001 - store errors are opaque
            raise VectorStoreError(
                f"Impossibile aprire l'indice in {self._persist_dir}: {exc}"
            ) from exc
        return self._client

    def _get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        try:
            collection = self._get_client().get_or_create_collection(
                name=self._collection_name,
                metadata=dict(_COLLECTION_METADATA),
                # We supply the vectors ourselves; without this Chroma downloads
                # its own ONNX model to compute them.
                embedding_function=None,
            )
        except Exception as exc:  # noqa: BLE001 - store errors are opaque
            raise VectorStoreError(
                f"Impossibile aprire la collection '{self._collection_name}' "
                f"in {self._persist_dir}: {exc}"
            ) from exc

        self._verify_metric(collection)
        self._collection = collection
        return collection

    def _verify_metric(self, collection: Any) -> None:
        """Refuse a collection that was created with a different distance metric.

        ``get_or_create_collection`` does not reconfigure a collection that
        already exists: an index built earlier with the default L2 space stays
        L2, silently, and every score this adapter derived from it would be
        meaningless. Better to stop and ask for a re-index.
        """
        space = (collection.metadata or {}).get(_SPACE_KEY)
        if space is None:
            logger.debug(
                "Metrica della collection '%s' non dichiarata nei metadati; "
                "si assume '%s'",
                self._collection_name,
                _COSINE,
            )
            return
        if space != _COSINE:
            raise VectorStoreError(
                f"L'indice in {self._persist_dir} usa la metrica '{space}' "
                f"invece di '{_COSINE}'.\n"
                "I punteggi di similarità sarebbero privi di significato e "
                "l'assistente rimanderebbe all'assistenza umana le domande a cui "
                "sa rispondere.\n"
                f"Eliminare la cartella {self._persist_dir} e ripetere "
                "l'indicizzazione."
            )


def _to_similarity(distance: float) -> float:
    """Cosine distance to a similarity in ``[0, 1]``, higher meaning more similar.

    Chroma's cosine distance is ``1 - cos(a, b)``. The clamp is not cosmetic:
    opposite vectors give a distance of 2 and hence a negative similarity, while
    an exact match can land a hair above 1.0 through floating point. Both would
    break the ``[0, 1]`` guarantee the port makes to the retriever.
    """
    return max(0.0, min(1.0, 1.0 - float(distance)))


def _to_metadata(chunk: Chunk) -> dict[str, str | int]:
    """Everything needed to rebuild a chunk without a second lookup.

    ``text`` is stored as Chroma's document rather than as metadata, and
    ``chunk_id`` is the Chroma id, so neither is duplicated here.
    """
    return {
        "doc_id": chunk.doc_id,
        "doc_title": chunk.doc_title,
        "section_title": chunk.section_title,
        "anchor": chunk.anchor,
        "ordinal": chunk.ordinal,
    }


def _rows(result: Any) -> list[tuple[Chunk, float]]:
    """Flatten Chroma's per-query lists back into chunks and distances."""
    ids = _first(result, "ids")
    documents = _first(result, "documents")
    metadatas = _first(result, "metadatas")
    distances = _first(result, "distances")

    rows: list[tuple[Chunk, float]] = []
    for chunk_id, text, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=False
    ):
        rows.append((_to_chunk(chunk_id, text, metadata or {}), distance))
    return rows


def _first(result: Any, key: str) -> list[Any]:
    """The first (and only) query's slice of a Chroma result, or an empty list."""
    values = result.get(key) if isinstance(result, dict) else None
    if not values:
        return []
    return list(values[0] or [])


def _to_chunk(chunk_id: str, text: str | None, metadata: dict[str, Any]) -> Chunk:
    missing = [field for field in _METADATA_FIELDS if field not in metadata]
    if missing:
        raise VectorStoreError(
            f"Il chunk '{chunk_id}' nell'indice è privo dei campi "
            f"{', '.join(missing)}.\n"
            "L'indice è stato scritto da una versione precedente del programma: "
            "eliminarlo e ripetere l'indicizzazione."
        )
    return Chunk(
        chunk_id=chunk_id,
        doc_id=str(metadata["doc_id"]),
        doc_title=str(metadata["doc_title"]),
        section_title=str(metadata["section_title"]),
        anchor=str(metadata["anchor"]),
        text=text or "",
        ordinal=int(metadata["ordinal"]),
    )
