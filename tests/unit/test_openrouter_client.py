"""The adapter's promise: a reasoning model's thinking never reaches the caller,
and an unparseable answer is an error rather than a guess.

The OpenAI client is replaced by a double, so nothing here touches the network.
What is exercised is the part that has to survive a model behaving badly.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from assistant.domain.models import Outcome
from assistant.generation.openrouter_client import LLMError, OpenRouterClient, _WireAnswer
from tests.conftest import make_retrieved

CONTEXT = (make_retrieved(doc_id="guida-esempio", anchor="primo-accesso"),)

VALID = json.dumps(
    {
        "outcome": "answer_found",
        "steps": ["Aprire la sezione **Schede**.", "Fare clic su **Nuova scheda**."],
        "citations": [{"doc_id": "guida-esempio", "anchor": "primo-accesso"}],
        "message": "",
    },
    ensure_ascii=False,
)

SECRET_REASONING = "RAGIONAMENTO-INTERNO-DEL-MODELLO"


class _FakeCompletions:
    def __init__(self, response: object) -> None:
        self._response = response
        self.kwargs: dict = {}

    def create(self, **kwargs: object):
        self.kwargs = kwargs
        return self._response


def _response(content: str | None, finish_reason: str = "stop", reasoning: str | None = None):
    message = SimpleNamespace(content=content, reasoning=reasoning)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)]
    )


def _client(response: object) -> tuple[OpenRouterClient, _FakeCompletions]:
    client = OpenRouterClient(
        model="modello-di-prova",
        base_url="https://esempio.invalid/api/v1",
        api_key="chiave-di-prova",
        temperature=0.1,
        max_tokens=100,
        timeout_seconds=30,
    )
    completions = _FakeCompletions(response)
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


@pytest.mark.parametrize(
    ("label", "content"),
    [
        ("json pulito", VALID),
        ("preceduto da <think>", f"<think>{SECRET_REASONING}</think>\n{VALID}"),
        ("dentro un recinto di codice", f"```json\n{VALID}\n```"),
        ("circondato da prosa", f"Ecco la risposta:\n{VALID}\nSpero sia utile."),
    ],
)
def test_the_answer_is_recovered_from_a_messy_response(label: str, content: str) -> None:
    client, _ = _client(_response(content, reasoning=SECRET_REASONING))

    draft = client.generate_answer("Come creo una scheda?", CONTEXT)

    assert draft.outcome is Outcome.ANSWER_FOUND, label
    assert len(draft.steps) == 2
    assert draft.citations[0].reference == "guida-esempio#primo-accesso"


def test_the_models_reasoning_never_reaches_the_draft() -> None:
    """Three independent measures, because any one of them can fail: the provider
    is asked not to return it, only ``message.content`` is read, and ``<think>``
    blocks are stripped."""
    client, completions = _client(
        _response(f"<think>{SECRET_REASONING}</think>\n{VALID}", reasoning=SECRET_REASONING)
    )

    draft = client.generate_answer("Come creo una scheda?", CONTEXT)

    assert SECRET_REASONING not in repr(draft)
    assert "think" not in repr(draft).lower()
    assert completions.kwargs["extra_body"]["reasoning"] == {"exclude": True}


def test_inline_markdown_is_preserved_in_the_steps() -> None:
    client, _ = _client(_response(VALID))

    draft = client.generate_answer("Come creo una scheda?", CONTEXT)

    assert "**Schede**" in draft.steps[0]


@pytest.mark.parametrize(
    ("label", "response"),
    [
        ("outcome fuori dall'enum", _response('{"outcome":"boh","steps":[],"citations":[],"message":"x"}')),
        ("campo mancante", _response('{"outcome":"answer_found","steps":[]}')),
        ("campo estraneo", _response('{"outcome":"answer_found","steps":[],"citations":[],"message":"","fonte":"x"}')),
        ("json troncato", _response('{"outcome":"answer_found","steps":["a"')),
        ("nessun json", _response("Non posso rispondere.")),
        ("contenuto vuoto", _response("")),
        ("solo ragionamento", _response(None, reasoning="pensavo...")),
        ("risposta troncata", _response(VALID, finish_reason="length")),
        ("nessuna scelta", SimpleNamespace(choices=[])),
    ],
)
def test_an_unusable_response_raises_instead_of_guessing(label: str, response: object) -> None:
    """Never a degraded draft: ``ports.py`` requires the caller to treat a failure
    as "no answer available", never as an empty answer."""
    client, _ = _client(response)

    with pytest.raises(LLMError):
        client.generate_answer("Come creo una scheda?", CONTEXT)


def test_a_truncated_response_says_which_setting_to_raise() -> None:
    client, _ = _client(_response(VALID, finish_reason="length"))

    with pytest.raises(LLMError, match="max_tokens"):
        client.generate_answer("Come creo una scheda?", CONTEXT)


def test_the_request_asks_for_a_strict_schema() -> None:
    client, completions = _client(_response(VALID))

    client.generate_answer("Come creo una scheda?", CONTEXT)

    response_format = completions.kwargs["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert completions.kwargs["extra_body"]["provider"] == {"require_parameters": True}


def test_the_context_is_sent_without_similarity_scores() -> None:
    """Scores would invite the model to reason about relevance, which the retriever
    has already decided against a calibrated threshold."""
    client, completions = _client(_response(VALID))

    client.generate_answer("Come creo una scheda?", CONTEXT)

    user_message = completions.kwargs["messages"][1]["content"]
    assert "doc_id: guida-esempio | anchor: primo-accesso" in user_message
    assert "0.9" not in user_message
    assert "score" not in user_message.lower()


def test_the_wire_schema_satisfies_strict_mode() -> None:
    """OpenAI's strict mode requires every property listed in ``required`` and
    ``additionalProperties: false``, including in nested definitions."""
    schema = _WireAnswer.model_json_schema()

    def check(node: dict, where: str) -> None:
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, where
            assert set(node.get("required", [])) == set(node.get("properties", {})), where
        for name, definition in node.get("$defs", {}).items():
            check(definition, name)

    check(schema, "root")


def test_an_empty_context_is_refused_before_any_call() -> None:
    """Asking the model with no documentation in front of it is exactly what the
    first gate exists to prevent."""
    client, completions = _client(_response(VALID))

    with pytest.raises(ValueError):
        client.generate_answer("Come creo una scheda?", ())

    assert completions.kwargs == {}
