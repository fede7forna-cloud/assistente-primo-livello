"""The embedder's contract, without downloading a model.

The real model is ~470 MB and is fetched from HuggingFace on first use, which does
not belong in a test suite. What is checked here is everything around it: that
construction costs nothing, that the two sides of the comparison are prefixed
differently, and that a failure is reported rather than swallowed.
"""

from __future__ import annotations

import pytest

from assistant.retrieval.local_embedder import EmbeddingError, LocalEmbedder


class _StubModel:
    max_seq_length = 512

    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.encoded: list[list[str]] = []

    def encode(self, texts, **kwargs):
        if self._error is not None:
            raise self._error
        self.encoded.append(list(texts))
        assert kwargs["normalize_embeddings"] is True
        return [[0.1, 0.2, 0.3] for _ in texts]

    def get_embedding_dimension(self) -> int:
        return 3


@pytest.fixture
def embedder() -> LocalEmbedder:
    return LocalEmbedder(
        model_name="modello-di-prova", query_prefix="query: ", passage_prefix="passage: "
    )


def test_construction_loads_nothing(embedder: LocalEmbedder) -> None:
    """Building the adapter must stay free: the first load may download hundreds of
    megabytes, and that has to happen when a command asks for it."""
    assert embedder._model is None


def test_an_empty_batch_does_not_touch_the_model(embedder: LocalEmbedder) -> None:
    assert embedder.embed_documents([]) == ()
    assert embedder._model is None


def test_warm_up_loads_the_model(embedder: LocalEmbedder, monkeypatch: pytest.MonkeyPatch) -> None:
    """A long-lived server must pay the load at start-up, not charge it to whoever
    asks the first question."""
    loads: list[int] = []

    def _load() -> _StubModel:
        loads.append(1)
        return _StubModel()

    monkeypatch.setattr(embedder, "_load_model", _load)

    embedder.warm_up()

    assert loads == [1]


def test_queries_and_passages_are_prefixed_differently(
    embedder: LocalEmbedder, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asymmetric models encode the two sides differently; using one prefix for both
    degrades retrieval quietly, which is why the port has two methods."""
    model = _StubModel()
    monkeypatch.setattr(embedder, "_load_model", lambda: model)

    embedder.embed_documents(["testo del documento"])
    embedder.embed_query("una domanda")

    assert model.encoded[0] == ["passage: testo del documento"]
    assert model.encoded[1] == ["query: una domanda"]


def test_vectors_are_plain_floats(embedder: LocalEmbedder, monkeypatch: pytest.MonkeyPatch) -> None:
    """Converting here keeps numpy out of every layer above, so nothing downstream
    can grow a dependency on it by accident."""
    monkeypatch.setattr(embedder, "_load_model", lambda: _StubModel())

    vector = embedder.embed_query("una domanda")

    assert all(type(value) is float for value in vector)


def test_an_encoding_failure_is_reported_with_the_model_name(
    embedder: LocalEmbedder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(embedder, "_load_model", lambda: _StubModel(error=RuntimeError("memoria")))

    with pytest.raises(EmbeddingError, match="modello-di-prova"):
        embedder.embed_query("una domanda")


def test_an_oversized_passage_is_flagged(
    embedder: LocalEmbedder, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Transformers truncate at ``max_seq_length`` without raising: a chunk that is
    too long loses its tail and nobody finds out."""
    monkeypatch.setattr(embedder, "_load_model", lambda: _StubModel())

    with caplog.at_level("WARNING"):
        embedder.embed_documents(["parola " * 5000])

    assert any("troncati" in record.message for record in caplog.records)
