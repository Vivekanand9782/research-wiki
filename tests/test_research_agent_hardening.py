"""Tests for hardened Research-Wiki Agent and LLM client.

Verifies:
1. agent._MAX_OBS_CHARS is 8000.
2. Fallback to clean deterministic hit list when LLM fails or reaches max turns.
3. answer.md NEVER contains raw tool JSON or [max turns reached].
4. transcript.json records meaningful observation data.
5. llm.py retry mechanism with backoff for HTTP 403 / 429 across keys.
"""

import io
import json
import urllib.error
from unittest.mock import patch, MagicMock
import pytest

from research_agent import agent, llm, wiki_tools


def test_max_obs_chars_is_8000():
    assert agent._MAX_OBS_CHARS == 8000


def test_is_valid_grounded_answer():
    assert not agent._is_valid_grounded_answer("")
    assert not agent._is_valid_grounded_answer("   ")
    assert not agent._is_valid_grounded_answer("Some text\n\n[max turns reached]")
    assert not agent._is_valid_grounded_answer('{"tool": "wiki_search", "args": {"query": "seed"}}')
    assert not agent._is_valid_grounded_answer('```json\n{"tool": "read_page"}\n```')
    
    assert agent._is_valid_grounded_answer("Seed dormancy in wheat is regulated by TaPHS1 and TaMFT.")
    assert agent._is_valid_grounded_answer("No evidence in the research-wiki supports this query.")


def test_agent_no_llm_clean_listing():
    with patch.object(llm, "has_key", return_value=False):
        res = agent.run("seed dormancy", top_k=3, use_llm=False, quiet=True)
    assert "# Results for: seed dormancy" in res
    assert "tools-only" in res
    assert "[max turns reached]" not in res
    assert "{" not in res.splitlines()[0]


def test_agent_llm_unavailable_falls_back_to_clean_hit_list(tmp_path):
    with patch.object(llm, "has_key", return_value=True), \
         patch.object(llm, "chat", side_effect=llm.LLMUnavailable("Network down")), \
         patch.object(agent, "HERE", tmp_path):
        res = agent.run("preharvest sprouting", top_k=3, use_llm=True, quiet=True)
    
    assert "# Results for: preharvest sprouting" in res
    assert "deterministic fallback" in res
    assert "[max turns reached]" not in res
    assert not res.strip().startswith("{")
    
    # Verify saved session
    saved_dirs = list((tmp_path / "output").glob("*"))
    assert len(saved_dirs) == 1
    answer_file = saved_dirs[0] / "answer.md"
    assert answer_file.exists()
    saved_text = answer_file.read_text()
    assert "# Results for: preharvest sprouting" in saved_text
    assert "[max turns reached]" not in saved_text
    assert not saved_text.strip().startswith("{")


def test_agent_max_turns_tool_call_falls_back_cleanly(tmp_path):
    # LLM always returns a tool call even on final synthesis
    tool_call_reply = '```json\n{"tool": "wiki_search", "args": {"query": "seed dormancy"}}\n```'
    
    with patch.object(llm, "has_key", return_value=True), \
         patch.object(llm, "chat", return_value=tool_call_reply), \
         patch.object(agent, "HERE", tmp_path):
        res = agent.run("seed dormancy", top_k=3, max_turns=2, use_llm=True, quiet=True)
        
    assert "# Results for: seed dormancy" in res
    assert "[max turns reached]" not in res
    assert not res.strip().startswith("{")
    
    saved_dirs = list((tmp_path / "output").glob("*"))
    assert len(saved_dirs) == 1
    transcript_file = saved_dirs[0] / "transcript.json"
    assert transcript_file.exists()
    transcript_data = json.loads(transcript_file.read_text())
    
    # Check that observations in transcript record meaningful structured data
    tool_steps = [s for s in transcript_data if "tool" in s]
    assert len(tool_steps) > 0
    for step in tool_steps:
        assert "observation" in step
        assert "observation_text" in step
        assert "observation_len" in step
        assert step["observation_len"] > 0


def test_llm_retries_and_backoff_on_429_and_403():
    keys = ["key-429", "key-403", "key-success"]
    with patch.object(llm, "_KEYS", keys), \
         patch.object(llm, "has_key", return_value=True), \
         patch.object(llm, "_parse_env", return_value=None), \
         patch.object(llm.time, "sleep") as mock_sleep:
        
        attempt = 0
        def fake_urlopen(req, timeout=120):
            nonlocal attempt
            attempt += 1
            auth = req.headers.get("Authorization", "")
            if "key-429" in auth:
                resp = MagicMock()
                resp.headers = {"Retry-After": "1"}
                raise urllib.error.HTTPError(req.full_url, 429, "Rate limit", resp.headers, io.BytesIO(b"{}"))
            if "key-403" in auth:
                raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, io.BytesIO(b"{}"))
            if "key-success" in auth:
                resp = MagicMock()
                resp.__enter__.return_value = resp
                resp.read.return_value = json.dumps({
                    "choices": [{"message": {"content": "Success!"}}]
                }).encode("utf-8")
                return resp
            raise ValueError(f"Unexpected auth: {auth}")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            res = llm.chat([{"role": "user", "content": "hi"}])
            assert res == "Success!"
            assert mock_sleep.called
            # Verify that sleep was called with Retry-After (1.0) and fast failover (0.05)
            sleep_args = [call[0][0] for call in mock_sleep.call_args_list]
            assert 1.0 in sleep_args
            assert 0.05 in sleep_args


def test_llm_stream_retries_and_backoff():
    keys = ["key-429", "key-success"]
    with patch.object(llm, "_KEYS", keys), \
         patch.object(llm, "has_key", return_value=True), \
         patch.object(llm, "_parse_env", return_value=None), \
         patch.object(llm.time, "sleep") as mock_sleep:
        
        def fake_urlopen(req, timeout=120):
            auth = req.headers.get("Authorization", "")
            if "key-429" in auth:
                resp = MagicMock()
                resp.headers = {"Retry-After": "0.5"}
                raise urllib.error.HTTPError(req.full_url, 429, "Rate limit", resp.headers, io.BytesIO(b"{}"))
            if "key-success" in auth:
                resp = MagicMock()
                resp.__enter__.return_value = resp
                resp.__iter__.return_value = iter([
                    b"data: {\"choices\": [{\"delta\": {\"content\": \"Stream \"}}]}\n",
                    b"data: {\"choices\": [{\"delta\": {\"content\": \"success\"}}]}\n",
                    b"data: [DONE]\n"
                ])
                return resp
            raise ValueError(f"Unexpected auth: {auth}")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            chunks = list(llm.chat_stream([{"role": "user", "content": "hi"}]))
            assert "".join(chunks) == "Stream success"
            assert mock_sleep.called
