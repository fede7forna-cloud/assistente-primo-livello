"""The adapter that can be wrong without anything crashing.

ChromaDB returns a *distance* — lower is closer — while ``ports.VectorStore``
promises a *similarity* in ``[0, 1]`` where higher is closer. An adapter that
leaked raw distances would invert the escalation threshold: the assistant would
answer from its least relevant sections and escalate the questions it could have
answered, with no exception raised and no test of the domain noticing.

These tests use a real ChromaDB on disk, in a temporary directory. Local files
only — no network.
"""

from __future__ import annotations

import pytest

from assistant.retrieval.chroma_store import ChromaVectorStore, VectorStoreError, _to_similarity
from tests.conftest import make_chunk

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture
def store(tmp_path) -> ChromaVectorStore:
    return ChromaVectorStore(persist_dir=tmp_path / "indice", collection_name="prova")


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(0.0, 1.0), (0.2, 0.8), (1.0, 0.0), (2.0, 0.0), (-1e-9, 1.0)],
)
def test_distance_becomes_a_similarity_inside_the_unit_interval(
    distance: float, expected: float
) -> None:
    """The clamp is not cosmetic: opposite vectors give a distance of 2 and hence a
    negative similarity, and an exact match can land a hair above 1.0."""
    similarity = _to_similarity(distance)

    assert similarity == pytest.approx(expected)
    assert 0.0 <= similarity <= 1.0


def test_a_perfect_match_scores_higher_than_an_unrelated_one(store: ChromaVectorStore) -> None:
    chunks = (
        make_chunk(anchor="alfa", text="testo alfa"),
        make_chunk(anchor="beta", text="testo beta", ordinal=1),
    )
    store.upsert(chunks, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    results = store.search([1.0, 0.0, 0.0], limit=2)

    assert [item.chunk.anchor for item in results] == ["alfa", "beta"]
    assert results[0].score == pytest.approx(1.0, abs=1e-6)
    assert results[0].score > results[1].score


def test_results_are_sorted_by_descending_similarity(store: ChromaVectorStore) -> None:
    chunks = tuple(
        make_chunk(anchor=f"sezione-{index}", text=f"testo {index}", ordinal=index)
        for index in range(3)
    )
    store.upsert(chunks, [[1.0, 0.0, 0.0], [0.7, 0.7, 0.0], [0.0, 1.0, 0.0]])

    scores = [item.score for item in store.search([1.0, 0.0, 0.0], limit=3)]

    assert scores == sorted(scores, reverse=True)


def test_upsert_is_idempotent(store: ChromaVectorStore) -> None:
    chunks = (make_chunk(anchor="alfa"),)
    store.upsert(chunks, [[1.0, 0.0, 0.0]])
    store.upsert(chunks, [[1.0, 0.0, 0.0]])

    assert store.count() == 1


def test_a_chunk_survives_the_round_trip(store: ChromaVectorStore) -> None:
    """A vector store hands back chunks in isolation, so everything a citation
    needs has to come back with them."""
    chunk = make_chunk(
        doc_id="procedure-esempio",
        anchor="archiviare-scheda",
        doc_title="Procedure di esempio",
        section_title="Archiviare una scheda",
        text="Aprire la scheda da archiviare.",
        ordinal=7,
    )
    store.upsert((chunk,), [[1.0, 0.0, 0.0]])

    restored = store.search([1.0, 0.0, 0.0], limit=1)[0].chunk

    assert restored == chunk


def test_clear_empties_the_index(store: ChromaVectorStore) -> None:
    store.upsert((make_chunk(),), [[1.0, 0.0, 0.0]])
    store.clear()

    assert store.count() == 0
    assert store.search([1.0, 0.0, 0.0], limit=3) == ()


def test_searching_an_empty_index_returns_nothing(store: ChromaVectorStore) -> None:
    assert store.search([1.0, 0.0, 0.0], limit=3) == ()


def test_mismatched_lengths_are_rejected(store: ChromaVectorStore) -> None:
    with pytest.raises(ValueError):
        store.upsert((make_chunk(), make_chunk(anchor="beta")), [[1.0, 0.0, 0.0]])


def test_an_index_built_with_another_metric_is_refused(tmp_path) -> None:
    """``get_or_create_collection`` does not reconfigure an existing collection: an
    index built with the default L2 space stays L2, silently, and every score
    derived from it would be meaningless."""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    path = tmp_path / "indice-l2"
    client = chromadb.PersistentClient(
        path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    client.create_collection(name="prova", metadata={"hnsw:space": "l2"}, embedding_function=None)
    del client

    with pytest.raises(VectorStoreError, match="metrica"):
        ChromaVectorStore(persist_dir=path, collection_name="prova").count()


def test_the_metric_error_says_what_to_do(tmp_path) -> None:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    path = tmp_path / "indice-l2"
    client = chromadb.PersistentClient(
        path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    client.create_collection(name="prova", metadata={"hnsw:space": "l2"}, embedding_function=None)
    del client

    with pytest.raises(VectorStoreError) as error:
        ChromaVectorStore(persist_dir=path, collection_name="prova").count()

    # The precise diagnosis must not be re-wrapped by the generic handler of the
    # calling method, or the instructions end up buried mid-sentence.
    assert str(error.value).startswith("L'indice")
    assert "ripetere l'indicizzazione" in str(error.value)


def test_an_invalid_limit_is_rejected(store: ChromaVectorStore) -> None:
    with pytest.raises(ValueError):
        store.search([1.0, 0.0, 0.0], limit=0)
