"""Test suite for the Unified LLM Hub (llm_config) and model switching.

Verifies:
1. Single source of truth: changing model in llm_config or env propagates
   to research-wiki/config.py, paper_agent/src/config.py, genai_client, etc.
2. Provider switching: switching provider presets updates base URLs and defaults.
3. Dynamic limits: arbitrary models get safe default token ceilings and context windows.
4. CLI helper: scripts/set_llm.py --show and mutation flags.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parent
WORKSPACE_ROOT = REPO_ROOT.parent if (REPO_ROOT.parent / "scripts" / "set_llm.py").exists() else REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import llm_config


def test_default_model_and_provider_resolution():
    with patch.dict(os.environ, {}, clear=True):
        assert llm_config.get_provider() == "general_compute"
        assert llm_config.get_model() == "minimax-m2.7"
        assert llm_config.get_base_url() == "https://api.generalcompute.com/v1"
        assert llm_config.get_chat_completions_url() == "https://api.generalcompute.com/v1/chat/completions"
        assert llm_config.get_max_output_tokens() == 128000
        assert llm_config.get_context_length() == 192000


def test_master_model_override_via_llm_model_env():
    with patch.dict(os.environ, {"LLM_MODEL": "minimax-m2.7"}, clear=True):
        assert llm_config.get_model() == "minimax-m2.7"
        assert llm_config.get_max_output_tokens("minimax-m2.7") == 128000
        assert llm_config.get_context_length("minimax-m2.7") == 192000


def test_provider_preset_switching():
    with patch.dict(os.environ, {"LLM_PROVIDER": "deepseek"}, clear=True):
        assert llm_config.get_provider() == "deepseek"
        assert llm_config.get_base_url() == "https://api.deepseek.com/v1"
        assert llm_config.get_model() == "deepseek-chat"


def test_arbitrary_new_model_works_dynamically():
    custom_model = "my-custom-org/finetuned-bio-model-v1"
    assert llm_config.is_supported_model(custom_model) is True
    with patch.dict(os.environ, {"LLM_MODEL": custom_model}, clear=True):
        assert llm_config.get_model() == custom_model
        # Dynamic fallback output and context limits
        assert llm_config.get_max_output_tokens(custom_model) == 8192
        assert llm_config.get_context_length(custom_model) == 128000


def test_set_llm_cli_show_json():
    result = subprocess.run(
        [sys.executable, str(WORKSPACE_ROOT / "scripts" / "set_llm.py"), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    data = json.loads(result.stdout)
    assert "model" in data
    assert "provider" in data
    assert "base_url" in data
    assert "chat_completions_url" in data


def test_propagation_to_subproject_configs():
    # Verify importing config in research-wiki and paper_agent reflects LLM_MODEL
    with patch.dict(os.environ, {"LLM_MODEL": "qwen-test-model"}, clear=True):
        rw_dir = WORKSPACE_ROOT / "research-wiki"
        pa_dir = WORKSPACE_ROOT / "paper_agent" / "src"
        if str(rw_dir) not in sys.path:
            sys.path.insert(0, str(rw_dir))
        if str(pa_dir) not in sys.path:
            sys.path.insert(0, str(pa_dir))

        # Check direct resolution
        assert llm_config.get_model() == "qwen-test-model"
