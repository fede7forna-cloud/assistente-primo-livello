"""Composition root: the one place that picks concrete adapters.

Every module below this one names ports. This module names ChromaDB,
sentence-transformers and OpenRouter, and nothing else does. Swapping an adapter
is an edit here plus a line of configuration.

It exists because both surfaces need the same object graph. The API cannot build
it by importing from ``cli.py`` — that would make the server depend on the
command line and drag Typer and Rich into its process — and it cannot live in
``service.py`` either, since that module deliberately knows only about protocols.
Two copies of the wiring would be worse than either: the day an adapter changes
its signature, one copy silently stays behind.
"""

from __future__ import annotations

from dataclasses import dataclass

from assistant.config import Settings
from assistant.generation.openrouter_client import OpenRouterClient
from assistant.ingestion.chunker import SectionChunker
from assistant.ingestion.markdown_loader import MarkdownDocumentLoader
from assistant.ingestion.pipeline import IngestionPipeline
from assistant.retrieval.chroma_store import ChromaVectorStore
from assistant.retrieval.local_embedder import LocalEmbedder
from assistant.retrieval.retriever import Retriever
from assistant.service import AssistantService


@dataclass(frozen=True, slots=True)
class Components:
    """The assembled application, plus the pieces a caller may need directly.

    ``service`` is what both surfaces use. ``embedder`` and ``store`` are exposed
    because the API has to warm the model up at start-up, and reaching it through
    a chain of delegations from the service would put an operational concern
    inside two classes that have nothing to do with it.
    """

    settings: Settings
    embedder: LocalEmbedder
    store: ChromaVectorStore
    service: AssistantService


def build_components(settings: Settings) -> Components:
    """Wire the adapters into a working assistant. No I/O happens here.

    Both adapters are lazy by construction — the model is not loaded and the
    index is not opened until something is asked of them — so building this
    graph is cheap and cannot fail for reasons the caller has not caused yet.
    """
    embedder = LocalEmbedder(
        model_name=settings.embedding.model,
        query_prefix=settings.embedding.query_prefix,
        passage_prefix=settings.embedding.passage_prefix,
    )
    store = ChromaVectorStore(
        persist_dir=settings.paths.vector_store,
        collection_name=settings.store.collection_name,
    )
    retriever = Retriever(
        embedder=embedder,
        store=store,
        top_k=settings.retrieval.top_k,
        similarity_threshold=settings.retrieval.similarity_threshold,
    )
    llm_client = OpenRouterClient(
        model=settings.llm.model,
        base_url=settings.llm.base_url,
        api_key=settings.openrouter_api_key.get_secret_value(),
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
        timeout_seconds=settings.llm.timeout_seconds,
    )
    return Components(
        settings=settings,
        embedder=embedder,
        store=store,
        # The same store object the retriever searches: one wiring, so a health
        # check and a question can never disagree about which index is in use.
        service=AssistantService(
            retriever=retriever, llm_client=llm_client, store=store
        ),
    )


def build_pipeline(settings: Settings) -> IngestionPipeline:
    """Wire the indexing side. Shares no state with :func:`build_components`."""
    return IngestionPipeline(
        loader=MarkdownDocumentLoader(settings.paths.docs_source),
        chunker=SectionChunker(
            max_chars=settings.chunking.max_chars,
            overlap_chars=settings.chunking.overlap_chars,
        ),
        embedder=LocalEmbedder(
            model_name=settings.embedding.model,
            query_prefix=settings.embedding.query_prefix,
            passage_prefix=settings.embedding.passage_prefix,
        ),
        store=ChromaVectorStore(
            persist_dir=settings.paths.vector_store,
            collection_name=settings.store.collection_name,
        ),
    )
