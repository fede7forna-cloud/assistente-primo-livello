"""Configuration is validated once, at start-up, with messages that say what to do.

These tests never read the developer's own ``.env``: the key is injected through
the environment and the real one is removed first, so the suite behaves the same
on a machine that has never been configured.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from assistant.config import ConfigError, load_settings

PROJECT_SETTINGS = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture
def settings_file(tmp_path: Path) -> Path:
    path = tmp_path / "settings.yaml"
    path.write_text(PROJECT_SETTINGS.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _load(
    settings_file: Path,
    replace: tuple[str, str] | None = None,
    key: str = "chiave-di-prova",
):
    """Load the shipped configuration, optionally with one line swapped out."""
    if replace is not None:
        old, new = replace
        text = settings_file.read_text(encoding="utf-8")
        assert old in text, f"riga da sostituire non trovata: {old!r}"
        settings_file.write_text(text.replace(old, new), encoding="utf-8")

    env_file = settings_file.parent / ".env"
    env_file.write_text(f"OPENROUTER_API_KEY={key}\n", encoding="utf-8")
    return load_settings(config_file=settings_file, env_file=env_file)


def test_the_shipped_configuration_is_valid(settings_file: Path) -> None:
    settings = _load(settings_file)

    assert settings.retrieval.top_k >= 1
    assert 0.0 <= settings.retrieval.similarity_threshold <= 1.0
    assert settings.llm.model
    assert settings.embedding.model


def test_the_api_key_is_not_exposed_by_repr(settings_file: Path) -> None:
    settings = _load(settings_file, key="chiave-segretissima")

    assert "chiave-segretissima" not in repr(settings)
    assert settings.openrouter_api_key.get_secret_value() == "chiave-segretissima"


def test_relative_paths_are_resolved_against_the_project_root(settings_file: Path) -> None:
    settings = _load(settings_file)

    assert settings.paths.docs_source.is_absolute()
    assert settings.paths.vector_store.is_absolute()


def test_a_missing_key_fails_with_instructions(settings_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
        load_settings(config_file=settings_file, env_file=tmp_path / "assente.env")


def test_a_missing_configuration_file_is_reported(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=x\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="non trovato"):
        load_settings(config_file=tmp_path / "assente.yaml", env_file=env_file)


def test_invalid_yaml_is_reported(tmp_path: Path) -> None:
    config_file = tmp_path / "settings.yaml"
    config_file.write_text("llm: [non chiuso\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=x\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="non valida"):
        load_settings(config_file=config_file, env_file=env_file)


def test_an_out_of_range_threshold_is_rejected(settings_file: Path) -> None:
    with pytest.raises(ConfigError):
        _load(settings_file, ("similarity_threshold: 0.80", "similarity_threshold: 1.5"))


def test_overlap_must_be_smaller_than_the_chunk(settings_file: Path) -> None:
    """Otherwise splitting a long section never terminates."""
    with pytest.raises(ConfigError, match="overlap_chars"):
        _load(settings_file, ("overlap_chars: 200", "overlap_chars: 2000"))


def test_url_template_defaults_to_absent(settings_file: Path) -> None:
    assert _load(settings_file).documentation.url_template is None


def test_a_valid_url_template_is_accepted(settings_file: Path) -> None:
    settings = _load(
        settings_file,
        ("url_template: null", 'url_template: "https://docs.esempio.it/{doc_id}#{anchor}"'),
    )

    assert settings.documentation.url_template == "https://docs.esempio.it/{doc_id}#{anchor}"


@pytest.mark.parametrize(
    ("label", "template"),
    [
        ("nessun segnaposto", '"https://docs.esempio.it/pagina"'),
        ("manca anchor", '"https://docs.esempio.it/{doc_id}"'),
        ("manca doc_id", '"https://docs.esempio.it/{anchor}"'),
    ],
)
def test_a_url_template_without_placeholders_is_rejected(
    settings_file: Path, label: str, template: str
) -> None:
    """A broken template would produce wrong links on every answer, in silence."""
    with pytest.raises(ConfigError, match="deve contenere"):
        _load(settings_file, ("url_template: null", f"url_template: {template}"))
