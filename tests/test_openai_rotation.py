"""Offline tests for the General Compute Research Wiki client."""

from __future__ import annotations

import base64
import os
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
import requests

import genai_client as gc



@pytest.fixture(autouse=True)
def _reset_general_compute_process_state():
    gc._reset_provider_circuit()
    gc._reset_http_session()
    with gc._request_times_lock:
        previous_request_times = list(gc._request_times)
        gc._request_times.clear()
    yield
    gc._reset_provider_circuit()
    gc._reset_http_session()
    with gc._request_times_lock:
        gc._request_times[:] = previous_request_times

class FakeResponse:
    def __init__(self, status_code=200, payload=None, *, text="", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def completion(text="ok"):
    return FakeResponse(payload={"choices": [{"message": {"content": text}}]})


def run_with(manager, session, **kwargs):
    with (
        patch.object(gc, "openai_rotating_client", manager),
        patch.object(gc, "_get_http_session", return_value=session),
        patch.object(gc.time, "sleep"),
    ):
        return gc.generate_content_with_retry(
            model=kwargs.pop("model", "gpt-oss-120b"),
            contents=kwargs.pop("contents", "prompt"),
            **kwargs,
        )


def test_general_compute_key_parsing_accepts_three_keys():
    env = {
        "LLM_API_KEYS": "",
        "GENERAL_COMPUTE_API_KEYS": "key1, key2\nkey3",
        "GENERAL_COMPUTE_API_KEY": "",
        "AEROLINK_API_KEYS": "",
        "HCN_SEC_API_KEYS": "",
    }
    with patch.dict(os.environ, env, clear=False):
        manager = gc.RotatingOpenAIClient()
    assert manager.keys == ["key1", "key2", "key3"]


def test_single_key_fallback_and_legacy_credentials_are_ignored():
    env = {
        "LLM_API_KEYS": "",
        "GENERAL_COMPUTE_API_KEYS": "",
        "GENERAL_COMPUTE_API_KEY": "only-general-compute",
        "AEROLINK_API_KEYS": "",
        "HCN_SEC_API_KEYS": "",
        "OPENAI_API_KEY": "must-not-be-loaded-either",
    }
    with patch.dict(os.environ, env, clear=False):
        assert gc.RotatingOpenAIClient().keys == ["only-general-compute"]

    env["GENERAL_COMPUTE_API_KEY"] = ""
    with patch.dict(os.environ, env, clear=False):
        assert gc.RotatingOpenAIClient().keys == []


def test_healthy_requests_round_robin_across_three_keys():
    manager = gc.RotatingOpenAIClient(["key1", "key2", "key3"])
    session = FakeSession([completion(str(i)) for i in range(4)])
    with (
        patch.object(gc, "openai_rotating_client", manager),
        patch.object(gc, "_get_http_session", return_value=session),
    ):
        for index in range(4):
            result = gc.generate_content_with_retry("gpt-oss-120b", "prompt", retries=1)
            assert result.text == str(index)

    auth = [call[1]["headers"]["Authorization"] for call in session.calls]
    assert auth == ["Bearer key1", "Bearer key2", "Bearer key3", "Bearer key1"]


def test_round_robin_selection_is_thread_safe():
    manager = gc.RotatingOpenAIClient(["key1", "key2", "key3"])
    with ThreadPoolExecutor(max_workers=12) as pool:
        selected = list(pool.map(lambda _: manager.acquire_key()[0], range(300)))
    assert Counter(selected) == {0: 100, 1: 100, 2: 100}


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("https://api.generalcompute.com/v1", "https://api.generalcompute.com/v1/chat/completions"),
        ("https://example.test/v1/", "https://example.test/v1/chat/completions"),
        ("https://example.test/v1/chat/completions", "https://example.test/v1/chat/completions"),
        ("https://example.test/v1/chat/completions/", "https://example.test/v1/chat/completions"),
    ],
)
def test_endpoint_normalization_never_duplicates_path(configured, expected):
    env = {
        "GENERAL_COMPUTE_BASE_URL": configured,
        "AEROLINK_BASE_URL": "",
        "HCN_SEC_BASE_URL": "",
    }
    with patch.dict(os.environ, env, clear=False):
        assert gc._get_general_compute_base_url() == expected


def test_only_two_working_models_are_accepted_before_transport():
    assert gc._resolve_model("gpt-oss-120b") == "gpt-oss-120b"
    assert gc._resolve_model("minimax-m2.7") == "minimax-m2.7"
    session = FakeSession([completion()])
    with (
        patch.object(gc, "openai_rotating_client", gc.RotatingOpenAIClient(["key1"])),
        patch.object(gc, "_get_http_session", return_value=session),
        pytest.raises(gc.GeneralComputeError, match="Unsupported General Compute model"),
    ):
        gc.generate_content_with_retry("gpt-4.1", "prompt", retries=1)
    assert session.calls == []


def test_multimodal_payload_uses_openai_image_url_data_uri():
    raw = b"offline-image-bytes"
    messages = gc._convert_to_openai_messages(
        [
            "inspect this figure",
            {"inline_data": {"mime_type": "image/png", "data": raw}},
        ],
        "be precise",
    )
    assert messages[0] == {"role": "system", "content": "be precise"}
    assert messages[1]["role"] == "user"
    assert messages[1]["content"][0] == {
        "type": "text",
        "text": "inspect this figure",
    }
    assert messages[1]["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
        },
    }


def test_system_generation_parameters_and_json_mode_are_forwarded():
    manager = gc.RotatingOpenAIClient(["key1"])
    session = FakeSession([completion("structured")])
    result = run_with(
        manager,
        session,
        retries=1,
        system_instruction="system rules",
        config_params={
            "temperature": 0.2,
            "top_p": 0.8,
            "max_output_tokens": 321,
            "response_mime_type": "application/json",
        },
    )
    assert result.text == "structured"
    payload = session.calls[0][1]["json"]
    assert payload == {
        "model": "gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "system rules"},
            {"role": "user", "content": "prompt"},
        ],
        "temperature": 0.2,
        "top_p": 0.8,
        "max_tokens": 321,
        "response_format": {"type": "json_object"},
    }
    assert isinstance(session.calls[0][1]["timeout"], tuple)


def test_minimax_defaults_to_split_reasoning_metadata():
    manager = gc.RotatingOpenAIClient(["key1"])
    session = FakeSession([completion("structured")])
    result = run_with(
        manager,
        session,
        model="minimax-m2.7",
        retries=1,
    )
    assert result.text == "structured"
    assert session.calls[0][1]["json"]["reasoning_split"] is True


def test_reasoning_controls_and_metadata_are_preserved():
    manager = gc.RotatingOpenAIClient(["key1"])
    response = FakeResponse(
        payload={
            "choices": [
                {
                    "message": {
                        "content": "structured",
                        "reasoning": "synthetic reasoning trace",
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    )
    session = FakeSession([response])
    result = run_with(
        manager,
        session,
        model="minimax-m2.7",
        retries=1,
        config_params={
            "reasoning_split": True,
            "thinking": {"type": "disabled"},
        },
    )
    assert result.text == "structured"
    assert result.reasoning == "synthetic reasoning trace"
    assert result.usage == {"prompt_tokens": 10, "completion_tokens": 20}
    payload = session.calls[0][1]["json"]
    assert payload["reasoning_split"] is True
    assert payload["thinking"] == {"type": "disabled"}


def test_reasoning_details_fallback_is_supported():
    data = {
        "choices": [
            {
                "message": {
                    "content": "answer",
                    "reasoning_details": [{"text": "part one"}, {"text": "part two"}],
                }
            }
        ]
    }
    assert gc._response_reasoning(data) == "part onepart two"


def test_429_retries_with_next_key_and_honors_retry_after():
    manager = gc.RotatingOpenAIClient(["key1", "key2", "key3"])
    session = FakeSession(
        [
            FakeResponse(429, text="rate limited", headers={"Retry-After": "2"}),
            completion("recovered"),
        ]
    )
    with (
        patch.object(gc, "openai_rotating_client", manager),
        patch.object(gc, "_get_http_session", return_value=session),
        patch.object(gc.time, "sleep") as sleep,
    ):
        result = gc.generate_content_with_retry("gpt-oss-120b", "prompt", retries=3)
    assert result.text == "recovered"
    assert [call[1]["headers"]["Authorization"] for call in session.calls] == [
        "Bearer key1",
        "Bearer key2",
    ]
    sleep.assert_called_once_with(2.0)


@pytest.mark.parametrize("status", [401, 403])
def test_auth_rejection_disables_exact_failed_key(status):
    manager = gc.RotatingOpenAIClient(["key1", "key2", "key3"])
    session = FakeSession([FakeResponse(status, text="sensitive provider body"), completion()])
    result = run_with(manager, session, retries=3)
    assert result.text == "ok"
    assert manager._disabled == {0}
    assert [call[1]["headers"]["Authorization"] for call in session.calls] == [
        "Bearer key1",
        "Bearer key2",
    ]


@pytest.mark.parametrize("status", [400, 404, 405, 422])
def test_permanent_request_errors_are_not_retried(status):
    manager = gc.RotatingOpenAIClient(["key1", "key2", "key3"])
    session = FakeSession([FakeResponse(status, text="do not expose this body")])
    with pytest.raises(gc.GeneralComputeError, match=f"HTTP {status}") as caught:
        run_with(manager, session, retries=4)
    assert len(session.calls) == 1
    assert "do not expose" not in str(caught.value)


def test_transport_attempt_cap_is_independent_of_key_count():
    manager = gc.RotatingOpenAIClient([f"key{i}" for i in range(20)])
    session = FakeSession([FakeResponse(503) for _ in range(3)])
    with (
        patch.object(gc.config, "AI_MAX_TRANSPORT_ATTEMPTS", 3),
        pytest.raises(gc.GeneralComputeError, match="after 3 attempts"),
    ):
        run_with(manager, session, retries=20)
    assert len(session.calls) == 3


@pytest.mark.parametrize(
    "first",
    [
        FakeResponse(200, payload=ValueError("bad json")),
        FakeResponse(200, payload={"choices": []}),
        requests.Timeout("offline timeout"),
    ],
)
def test_invalid_or_transient_response_is_retried(first):
    manager = gc.RotatingOpenAIClient(["key1", "key2"])
    session = FakeSession([first, completion("recovered")])
    assert run_with(manager, session, retries=2).text == "recovered"
    assert len(session.calls) == 2


def test_context_error_switches_to_long_context_model_once():
    manager = gc.RotatingOpenAIClient(["key1", "key2"])
    session = FakeSession(
        [
            FakeResponse(400, text="maximum context length exceeded"),
            completion("long result"),
        ]
    )
    # .env may legitimately export long-context model env vars; the config
    # attribute under test only applies when those are unset.
    env_vars = ["AEROLINK_LONG_CONTEXT_MODEL", "GENERAL_COMPUTE_LONG_CONTEXT_MODEL"]
    with patch.object(gc.config, "GENERAL_COMPUTE_LONG_CONTEXT_MODEL", "minimax-m2.7"), \
         patch.dict(os.environ, {k: "" for k in env_vars}):
        for k in env_vars:
            os.environ.pop(k, None)
        result = run_with(manager, session, model="gpt-oss-120b", retries=2)
    assert result.text == "long result"
    assert [call[1]["json"]["model"] for call in session.calls] == [
        "gpt-oss-120b",
        "minimax-m2.7",
    ]


def test_final_error_is_sanitized_and_never_contains_key_or_body():
    manager = gc.RotatingOpenAIClient(["dummy-secret-key"])
    session = FakeSession([FakeResponse(503, text="body-secret-value")])
    with pytest.raises(gc.GeneralComputeError) as caught:
        run_with(manager, session, retries=1)
    message = str(caught.value)
    assert "dummy-secret-key" not in message
    assert "body-secret-value" not in message
    assert "HTTP 503" in message


def test_request_budget_reservation_blocks_until_a_slot_is_freed():
    with patch.object(gc.config, "GENERAL_COMPUTE_MAX_REQ_PER_WINDOW", 1):
        gc._reserve_request_slot()
        sleeping = threading.Event()
        release_sleep = threading.Event()
        completed = threading.Event()

        def pause_until_released(_seconds):
            sleeping.set()
            release_sleep.wait(timeout=1)

        def reserve_second_slot():
            gc._reserve_request_slot()
            completed.set()

        with patch.object(gc.time, "sleep", side_effect=pause_until_released):
            worker = threading.Thread(target=reserve_second_slot)
            worker.start()
            assert sleeping.wait(timeout=1)
            with gc._request_times_lock:
                assert len(gc._request_times) == 1
            assert not completed.is_set()
            with gc._request_times_lock:
                gc._request_times.clear()
            release_sleep.set()
            worker.join(timeout=1)

    assert completed.is_set()
    assert not worker.is_alive()


def test_thinking_config_merges_template_options_and_preserves_precedence():
    class DisabledThinking:
        type = "disabled"

    assert gc._is_thinking_enabled(DisabledThinking()) is False
    assert gc._is_thinking_enabled({"enabled": True}) is True

    manager = gc.RotatingOpenAIClient(["key1"])
    session = FakeSession([completion("structured")])
    run_with(
        manager,
        session,
        retries=1,
        config_params={
            "thinking": {"type": "enabled"},
            "chat_template_kwargs": {"from_config": True},
        },
        thinking={"type": "disabled"},
        chat_template_kwargs={"from_call": True, "enable_thinking": True},
    )

    payload = session.calls[0][1]["json"]
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["chat_template_kwargs"] == {
        "from_config": True,
        "from_call": True,
        "enable_thinking": False,
    }


def test_extract_params_accepts_both_max_token_names():
    class Params:
        max_output_tokens = 1234

    assert gc._extract_params(Params())["max_tokens"] == 1234
    assert gc._extract_params({"max_tokens": 5678})["max_tokens"] == 5678


def test_rate_limit_classifier_compatibility():
    assert gc._is_openai_depletion_error(Exception("Rate limit exceeded")) is True
    assert gc._is_openai_depletion_error(Exception("Resource exhausted quota")) is True
    assert gc._is_openai_depletion_error(Exception("429 Too Many Requests")) is True
    assert gc._is_openai_depletion_error(Exception("Normal value error")) is False


def test_models_proxy_preserves_generate_content_api():
    manager = gc.RotatingOpenAIClient(["key1"])
    session = FakeSession([completion("proxy result")])
    with (
        patch.object(gc, "openai_rotating_client", manager),
        patch.object(gc, "_get_http_session", return_value=session),
        patch.object(gc.time, "sleep"),
    ):
        response = gc.genai_client.models.generate_content(
            model="gpt-oss-120b",
            contents="prompt",
            config={"max_output_tokens": 20},
            retries=1,
        )
    assert response.text == "proxy result"


def test_auth_rejections_try_every_key_without_spending_transport_budget():
    manager = gc.RotatingOpenAIClient([f"key{i}" for i in range(1, 7)])
    session = FakeSession(
        [FakeResponse(401, text="rejected") for _ in range(5)]
        + [completion("sixth key works")]
    )
    result = run_with(manager, session, retries=1)
    assert result.text == "sixth key works"
    assert len(session.calls) == 6
    assert manager._disabled == {0, 1, 2, 3, 4}


def test_output_tokens_are_clamped_to_documented_model_limit():
    manager = gc.RotatingOpenAIClient(["key1"])
    session = FakeSession([completion("bounded")])
    result = run_with(
        manager,
        session,
        retries=1,
        config_params={"max_output_tokens": 16_384},
    )
    assert result.text == "bounded"
    assert session.calls[0][1]["json"]["max_tokens"] == 8192


def test_transport_error_resets_thread_local_http_session_before_retry():
    manager = gc.RotatingOpenAIClient(["key1", "key2"])
    session = FakeSession([requests.ConnectionError("stale socket"), completion("ok")])
    with patch.object(gc, "_reset_http_session") as reset_session:
        result = run_with(manager, session, retries=2)
    assert result.text == "ok"
    reset_session.assert_called_once_with()


def test_exhausted_transient_failure_opens_shared_outage_circuit():
    manager = gc.RotatingOpenAIClient(["key1"])
    failed_session = FakeSession([requests.Timeout("provider unavailable")])
    with (
        patch.object(gc.config, "GENERAL_COMPUTE_OUTAGE_COOLDOWN_SECONDS", 30),
        pytest.raises(gc.GeneralComputeError, match="after 1 attempts"),
    ):
        run_with(manager, failed_session, retries=1)

    queued_session = FakeSession([completion("must not be called")])
    with (
        patch.object(gc, "openai_rotating_client", manager),
        patch.object(gc, "_get_http_session", return_value=queued_session),
        pytest.raises(gc.GeneralComputeError, match="temporarily unavailable") as caught,
    ):
        gc.generate_content_with_retry("gpt-oss-120b", "prompt", retries=1)
    assert caught.value.retryable is True
    assert queued_session.calls == []
