"""Command line interface: a thin shell over ``AssistantService``.

Two responsibilities and no third one. It wires the adapters together from
``Settings``, and it presents what comes back. No decision about relevance,
citations or escalation is taken here — those live one layer down, so that the
API can take them identically.

Presentation is not a detail in this project. The customer's requirement is
"numbered steps and clickable links to the section", and the model deliberately
returns neither: steps arrive unnumbered and citations arrive as ``doc_id`` plus
``anchor``. Numbering them and turning the reference into a link is this file's
job, and the API's, each in its own medium.

Errors from the layers below are printed as they are. ``LLMError``,
``EmbeddingError``, ``VectorStoreError``, ``ConfigError`` and
``MarkdownFormatError`` already carry Italian text written for whoever is at the
terminal; rewording them here would only lose detail.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.markdown import Markdown

from assistant.config import ConfigError, load_settings
from assistant.domain.models import Answer, Citation, Outcome
from assistant.factory import build_components, build_pipeline
from assistant.generation.openrouter_client import LLMError
from assistant.ingestion.markdown_loader import MarkdownFormatError
from assistant.ingestion.pipeline import IngestionError
from assistant.retrieval.chroma_store import VectorStoreError
from assistant.retrieval.local_embedder import EmbeddingError

app = typer.Typer(
    help="Assistente di primo livello: risponde solo sulla base della documentazione indicizzata.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)

# Every error a user can legitimately cause, plus every misconfiguration. All of
# them carry a message meant to be read as-is.
_USER_FACING_ERRORS = (
    ConfigError,
    MarkdownFormatError,
    IngestionError,
    EmbeddingError,
    VectorStoreError,
    LLMError,
)


@app.command()
def ingest(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostra il log dettagliato."),
) -> None:
    """Indicizza la documentazione presente in docs_source/."""
    _configure_logging(verbose)
    with _reporting_errors():
        settings = load_settings()
        pipeline = build_pipeline(settings)

        console.print(f"Documentazione: [bold]{settings.paths.docs_source}[/bold]")
        console.print(f"Modello di embedding: [bold]{settings.embedding.model}[/bold]")
        console.print(
            "[dim]Al primo avvio il modello viene scaricato da HuggingFace.[/dim]\n"
        )

        with console.status("Indicizzazione in corso..."):
            report = pipeline.run()

        console.print(
            f"[green]Fatto.[/green] {report.documents} documenti, "
            f"{report.sections} sezioni, {report.chunks} blocchi indicizzati."
        )
        console.print(f"Indice: [bold]{settings.paths.vector_store}[/bold]")


@app.command()
def ask(
    question: str = typer.Argument(..., help="La domanda da porre all'assistente."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostra il log dettagliato."),
) -> None:
    """Fai una domanda all'assistente."""
    _configure_logging(verbose)
    if not question.strip():
        err_console.print("La domanda non può essere vuota.", style="red")
        raise typer.Exit(code=1)

    with _reporting_errors():
        settings = load_settings()
        components = build_components(settings)

        with console.status("Cerco nella documentazione..."):
            answer = components.service.ask(question)

        _render(answer, settings.paths.docs_source)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Indirizzo su cui ascoltare."),
    port: int = typer.Option(8000, help="Porta su cui ascoltare."),
    reload: bool = typer.Option(False, "--reload", help="Riavvia a ogni modifica del codice."),
) -> None:
    """Avvia l'API HTTP (documentazione interattiva su /docs)."""
    # The configuration is read here only to fail before uvicorn takes over the
    # terminal: a missing API key should surface as this project's own message,
    # not as a traceback from inside a worker.
    with _reporting_errors():
        load_settings()

    console.print(f"API su [bold]http://{host}:{port}[/bold]")
    console.print(f"Documentazione interattiva: [bold]http://{host}:{port}/docs[/bold]")
    console.print("[dim]Il modello di embedding viene caricato all'avvio.[/dim]")
    # An import string rather than the app object: uvicorn needs to re-import the
    # module on each reload, and an object cannot be re-imported.
    uvicorn.run("assistant.api.app:app", host=host, port=port, reload=reload)


# --------------------------------------------------------------------------- #
# Presentation
# --------------------------------------------------------------------------- #


# Symbol, label and colour per outcome. The symbol and the words carry the
# meaning; the colour only reinforces it. An outcome shown in colour alone
# disappears into a pipe, a log file or a redirect — and with it the difference
# between "the documentation does not cover this" and "tell me more".
_BANNERS = {
    Outcome.ANSWER_FOUND: ("[OK]", "Risposta trovata nella documentazione", "green"),
    Outcome.NOT_IN_DOCUMENTATION: (
        "[!]",
        "Non presente in documentazione — rinvio all'assistenza",
        "yellow",
    ),
    Outcome.AMBIGUOUS_QUESTION: ("[?]", "Serve un chiarimento", "cyan"),
}


def _render(answer: Answer, docs_dir: Path) -> None:
    symbol, label, style = _BANNERS[answer.outcome]
    console.print()
    console.print(f"[{style}]{symbol} {label}[/{style}]")
    console.print()

    if answer.outcome is not Outcome.ANSWER_FOUND:
        console.print(answer.message, markup=False)
        return

    if answer.message:
        console.print(answer.message, markup=False)
        console.print()
    console.print(_numbered(answer.steps))
    console.print("[bold]Fonti[/bold]")
    for citation in answer.citations:
        console.print(f"  • {_source_line(citation, docs_dir)}")


def _numbered(steps: tuple[str, ...]) -> Markdown:
    """Number the steps and let Markdown render what the model wrote inside them.

    The model is told not to number its own steps — numbering is presentation,
    and a step that arrived pre-numbered would be numbered twice. It does use
    inline Markdown for the names of buttons and fields, which is worth rendering
    rather than stripping: bold is exactly how the documentation distinguishes a
    control from prose, and showing raw asterisks would lose that distinction.

    Each step is flattened to a single line first, so that a stray newline cannot
    break out of its list item and renumber everything after it.
    """
    lines = [f"{position}. {' '.join(step.split())}" for position, step in enumerate(steps, 1)]
    return Markdown("\n".join(lines))


def _source_line(citation: Citation, docs_dir: Path) -> str:
    """A citation as a readable label plus its reference, linked when possible.

    The reference ``doc_id#anchor`` is the project's citation contract, and the
    loader guarantees the document lives at ``docs_dir/<doc_id>.md`` — which is
    what makes a real, clickable file link possible here rather than a decorative
    one. A loader reading from somewhere other than a filesystem simply produces
    no link, and the reference is still printed.
    """
    label = f"{citation.section_title} — [dim]{citation.reference}[/dim]"
    document = docs_dir / f"{citation.doc_id}.md"
    if not document.is_file():
        return label
    return f"[link={document.as_uri()}#{citation.anchor}]{label}[/link]"


# --------------------------------------------------------------------------- #
# Plumbing
# --------------------------------------------------------------------------- #


@contextmanager
def _reporting_errors() -> Iterator[None]:
    """Print the message the layer below wrote, and exit non-zero.

    ``markup=False`` matters: these messages contain filesystem paths, and a
    Windows path with brackets would otherwise be swallowed as Rich markup.
    """
    try:
        yield
    except _USER_FACING_ERRORS as exc:
        err_console.print()
        err_console.print(str(exc), style="red", markup=False)
        raise typer.Exit(code=1) from exc


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if not verbose:
        return
    # These two are chatty enough to bury our own lines at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


if __name__ == "__main__":
    app()
