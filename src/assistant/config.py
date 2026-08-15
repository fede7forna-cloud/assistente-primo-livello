"""Application configuration.

Two sources, kept deliberately apart:

* ``.env`` holds secrets and is never committed;
* ``config/settings.yaml`` holds everything else and is version-controlled.

No API key, endpoint, model name, threshold or path is written in a ``.py``
file anywhere in this project: every one of them arrives through ``Settings``.
That is what makes the demo configurable without a code change, and what keeps
credentials out of the repository by construction rather than by discipline.

Configuration is validated once, at start-up, and failures are reported with a
message that says what to do about them — a missing key must not surface later
as an authentication error in the middle of a user's question.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
"""Repository root: ``src/assistant/config.py`` → ``src/assistant`` → ``src`` → root."""

DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


class ConfigError(RuntimeError):
    """Configuration is missing or invalid; the application cannot start.

    Carries a message written for whoever is running the command, in Italian
    like every other user-facing string, and it is expected to be printed as-is
    by the CLI and the API start-up hook.
    """


_MISSING_API_KEY = """\
Configurazione incompleta: manca OPENROUTER_API_KEY.

Senza una chiave API l'assistente non può interrogare il modello, quindi non
viene avviato.

Come procedere:
  1. Copiare il file di esempio:   cp .env.example .env
  2. Aprire .env e inserire la propria chiave in OPENROUTER_API_KEY
  3. Rilanciare il comando

La chiave si ottiene da https://openrouter.ai/keys
File .env cercato in: {env_file}\
"""

_MISSING_CONFIG_FILE = """\
Configurazione incompleta: file non trovato.

Il file dei parametri non è presente nel percorso atteso:
  {config_file}

Il file fa parte del progetto e dovrebbe essere già versionato: se manca,
verificare di trovarsi nella cartella corretta del repository.\
"""

_INVALID_CONFIG_FILE = """\
Configurazione non valida: {config_file}

{details}

Correggere i valori segnalati e rilanciare il comando.\
"""


class LLMSettings(BaseModel):
    """Which model answers, through which endpoint, and within which limits."""

    model_config = ConfigDict(frozen=True)

    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1)
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)


class EmbeddingSettings(BaseModel):
    """Which embedding model turns text into vectors, and how it is prompted.

    The prefixes exist because asymmetric models — the e5 family among them —
    encode a question and a passage differently. Keeping them in configuration
    rather than in the adapter means switching to a symmetric model is two empty
    strings, not a code change.
    """

    model_config = ConfigDict(frozen=True)

    model: str = Field(min_length=1)
    query_prefix: str = ""
    passage_prefix: str = ""


class RetrievalSettings(BaseModel):
    """The two numbers that decide when the assistant escalates.

    ``similarity_threshold`` is calibrated against the embedding model named in
    :class:`EmbeddingSettings`; the two cannot be changed independently. See the
    comments in ``config/settings.yaml`` for the calibration procedure.
    """

    model_config = ConfigDict(frozen=True)

    top_k: int = Field(ge=1, le=50)
    similarity_threshold: float = Field(ge=0.0, le=1.0)


class ChunkingSettings(BaseModel):
    """Size limits applied to sections that are too long to index whole."""

    model_config = ConfigDict(frozen=True)

    max_chars: int = Field(ge=200)
    overlap_chars: int = Field(ge=0)

    @field_validator("overlap_chars")
    @classmethod
    def _overlap_smaller_than_chunk(cls, value: int, info: ValidationInfo) -> int:
        max_chars = info.data.get("max_chars")
        if max_chars is not None and value >= max_chars:
            raise ValueError(
                f"overlap_chars ({value}) deve essere minore di max_chars ({max_chars}), "
                "altrimenti la suddivisione dei testi lunghi non termina"
            )
        return value


class DocumentationSettings(BaseModel):
    """Where the documentation is published, if it is published at all.

    Only the HTTP API uses this. The CLI links to the local files directly,
    which the API cannot do: a ``file://`` URL built on the server is dead on
    the client's machine and leaks the server's filesystem layout along the way.

    A template rather than a base URL because the published shape is not
    guessable — extension, path prefix and anchor format all vary — and a wrong
    guess produces broken links on every answer rather than an error.
    """

    model_config = ConfigDict(frozen=True)

    url_template: str | None = None

    @field_validator("url_template")
    @classmethod
    def _has_placeholders(cls, value: str | None) -> str | None:
        if value is None:
            return None
        missing = [token for token in ("{doc_id}", "{anchor}") if token not in value]
        if missing:
            raise ValueError(
                f"deve contenere {' e '.join(missing)} "
                '(es. "https://docs.esempio.it/{doc_id}#{anchor}"): senza segnaposto '
                "l'API restituirebbe lo stesso indirizzo per ogni citazione"
            )
        return value


class StoreSettings(BaseModel):
    """Identifies the collection inside the vector store."""

    model_config = ConfigDict(frozen=True)

    collection_name: str = Field(min_length=1)


class PathsSettings(BaseModel):
    """Where the documentation is read from and where the index is written.

    Relative paths in the YAML file are resolved against the project root, so
    the application behaves the same whatever directory it is launched from.
    """

    model_config = ConfigDict(frozen=True)

    docs_source: Path
    vector_store: Path

    @field_validator("docs_source", "vector_store")
    @classmethod
    def _make_absolute(cls, value: Path) -> Path:
        return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()


class Settings(BaseModel):
    """Every configurable value in the application, validated and frozen."""

    model_config = ConfigDict(frozen=True)

    llm: LLMSettings
    embedding: EmbeddingSettings
    retrieval: RetrievalSettings
    chunking: ChunkingSettings
    store: StoreSettings
    paths: PathsSettings
    documentation: DocumentationSettings = DocumentationSettings()
    openrouter_api_key: SecretStr


class _Secrets(BaseSettings):
    """Secrets read from the environment, or from ``.env`` when present.

    Held as ``SecretStr`` so the key cannot leak into a log line, a traceback or
    a ``repr`` of the settings object.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    openrouter_api_key: SecretStr


def load_settings(
    config_file: Path | None = None,
    env_file: Path | None = None,
) -> Settings:
    """Read, merge and validate the configuration.

    Raises:
        ConfigError: with a message meant to be shown to the user as-is,
            whenever the YAML file is missing or malformed, or the API key has
            not been provided.
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    env_file = env_file or DEFAULT_ENV_FILE

    if not config_file.is_file():
        raise ConfigError(_MISSING_CONFIG_FILE.format(config_file=config_file))

    try:
        raw = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(
            _INVALID_CONFIG_FILE.format(config_file=config_file, details=exc)
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigError(
            _INVALID_CONFIG_FILE.format(
                config_file=config_file,
                details="Il contenuto del file non è una mappa di sezioni.",
            )
        )

    # An absent .env is not an error: the key may come from the real environment,
    # which is how the application is expected to be configured in production.
    try:
        secrets = _Secrets(_env_file=env_file if env_file.is_file() else None)
    except ValidationError as exc:
        raise ConfigError(_MISSING_API_KEY.format(env_file=env_file)) from exc

    if not secrets.openrouter_api_key.get_secret_value().strip():
        raise ConfigError(_MISSING_API_KEY.format(env_file=env_file))

    try:
        return Settings(**raw, openrouter_api_key=secrets.openrouter_api_key)
    except ValidationError as exc:
        raise ConfigError(
            _INVALID_CONFIG_FILE.format(config_file=config_file, details=exc)
        ) from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application settings, parsed once per process.

    Cached because the API resolves settings on every request and re-reading
    two files each time would be waste; tests that need a different
    configuration call :func:`load_settings` directly instead.
    """
    return load_settings()
