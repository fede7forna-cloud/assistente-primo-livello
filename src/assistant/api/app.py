"""HTTP surface: a thin shell over the same ``AssistantService`` the CLI uses.

No decision about relevance, citations or escalation is taken here. What this
module does own is the translation between the application's vocabulary and
HTTP's — and that translation carries one rule worth stating plainly:

**an escalation is a 200; a fault is a 503.**

"The documentation does not cover this" is a correct answer, and a client that
saw it as an error would retry a question that will never succeed. Conversely, a
provider outage returned as a 200 with an escalation payload would tell the
client the documentation has a hole it does not have, and would break every
monitor downstream. The two are kept apart here because nothing below this layer
can tell them apart on the client's behalf.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from assistant.api.schemas import ChatRequest, ChatResponse, HealthResponse
from assistant.config import load_settings
from assistant.factory import Components, build_components
from assistant.generation.openrouter_client import LLMError
from assistant.retrieval.chroma_store import VectorStoreError
from assistant.retrieval.local_embedder import EmbeddingError

logger = logging.getLogger(__name__)

_UNAVAILABLE = 503

_DESCRIPTION = """\
Assistente di primo livello: risponde alle domande degli utenti **esclusivamente**
sulla base della documentazione indicizzata.

Ogni risposta operativa arriva in passaggi ordinati e cita le sezioni da cui
proviene. Quando la documentazione non copre la domanda, l'assistente lo dichiara
e rimanda all'assistenza umana invece di inventare.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the application once, and load the embedding model before serving.

    The model takes tens of seconds to load the first time. Doing it here means
    the cost falls on start-up, where a deployment expects it, instead of on
    whoever happens to ask the first question.

    A configuration error raised here stops the server from starting at all. That
    is deliberate: a process that boots and then fails every request is harder to
    notice than one that refuses to boot and says why.
    """
    components = build_components(load_settings())
    logger.info("Caricamento del modello di embedding...")
    components.embedder.warm_up()
    app.state.components = components
    logger.info("Assistente pronto")
    yield


app = FastAPI(
    title="Assistente di primo livello",
    description=_DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)


@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Fai una domanda all'assistente",
    responses={
        _UNAVAILABLE: {
            "description": (
                "Un componente non è disponibile (modello di linguaggio, modello "
                "di embedding o indice). Non è un giudizio sulla documentazione: "
                "la stessa domanda può avere successo più tardi."
            )
        }
    },
)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """Rispondi a una domanda usando solo la documentazione indicizzata."""
    components = _components(http_request)
    answer = components.service.ask(request.question)
    return ChatResponse.from_domain(
        answer, components.settings.documentation.url_template
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Stato del servizio",
    responses={
        _UNAVAILABLE: {
            "description": (
                "L'indice è vuoto o illeggibile. Con un indice vuoto l'assistente "
                "rimanderebbe all'assistenza qualunque domanda, quindi il servizio "
                "si dichiara non pronto."
            )
        }
    },
)
def health(http_request: Request) -> JSONResponse:
    """Riporta se il servizio è in grado di rispondere."""
    components = _components(http_request)
    indexed = components.service.index_size()
    body = HealthResponse(
        status="ok" if indexed else "degraded",
        indexed_chunks=indexed,
        model=components.settings.llm.model,
        embedding_model=components.settings.embedding.model,
    )
    return JSONResponse(
        content=body.model_dump(),
        status_code=200 if indexed else _UNAVAILABLE,
    )


def _components(request: Request) -> Components:
    return request.app.state.components


def _unavailable(request: Request, exc: Exception) -> JSONResponse:
    """Report an infrastructure fault, keeping the adapter's own wording.

    Those messages were written for a human and say what to check — a key in
    ``.env``, a timeout in the configuration, an index to rebuild. Rephrasing
    them here would replace a specific instruction with a generic apology.
    """
    logger.warning("%s: %s", type(exc).__name__, exc)
    return JSONResponse(content={"detail": str(exc)}, status_code=_UNAVAILABLE)


for _error in (LLMError, EmbeddingError, VectorStoreError):
    app.add_exception_handler(_error, _unavailable)
