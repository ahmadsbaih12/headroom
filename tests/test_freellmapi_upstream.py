"""``--freellmapi-url`` expands to the OpenAI + Anthropic upstreams."""

from __future__ import annotations

import pytest

from headroom.proxy.helpers import (
    classify_openai_upstream,
    resolve_freellmapi_upstream,
)


def _resolve(url, **kw):
    kw.setdefault("anthropic_api_url", None)
    kw.setdefault("openai_api_url", None)
    kw.setdefault("provider_name", None)
    return resolve_freellmapi_upstream(url, **kw)


def test_unset_returns_inputs_unchanged() -> None:
    assert _resolve(None, openai_api_url="https://x/v1") == (None, "https://x/v1", None)


@pytest.mark.parametrize(
    "url", ["http://localhost:3001", "http://localhost:3001/", "http://localhost:3001/v1"]
)
def test_sets_both_upstreams_and_name(url: str) -> None:
    assert _resolve(url) == (
        "http://localhost:3001",
        "http://localhost:3001/v1",
        "FreeLLMAPI",
    )


def test_explicit_values_win() -> None:
    assert _resolve(
        "http://localhost:3001",
        anthropic_api_url="https://a",
        openai_api_url="https://o/v1",
        provider_name="Mine",
    ) == ("https://a", "https://o/v1", "Mine")


def test_hosted_router_is_labelled() -> None:
    assert classify_openai_upstream("https://freellmapi.co/v1") == "FreeLLMAPI"
