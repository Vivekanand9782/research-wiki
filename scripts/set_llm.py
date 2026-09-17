#!/usr/bin/env python3
"""Unified LLM Management CLI for Antigravity Workspace.

Allows inspecting active LLM settings and switching models, providers, base URLs,
and API keys in ONE place, automatically propagating to all workspace scripts.

Usage:
    # 1. Inspect current settings
    python3 scripts/set_llm.py --show

    # 2. Switch active model across all scripts
    python3 scripts/set_llm.py --model minimax-m2.7
    python3 scripts/set_llm.py --model claude-opus-5-thinking
    python3 scripts/set_llm.py --model gpt-4o

    # 3. Switch provider preset
    python3 scripts/set_llm.py --provider deepseek --model deepseek-chat
    python3 scripts/set_llm.py --provider justwoker --model claude-opus-5-thinking

    # 4. Set custom base URL and API keys
    python3 scripts/set_llm.py --base-url https://api.custom.com/v1 --keys "sk-key1,sk-key2"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import llm_config


def print_status():
    summary = llm_config.get_config_summary()
    print("=" * 70)
    print("🤖 ANTIGRAVITY UNIFIED LLM HUB — ACTIVE CONFIGURATION")
    print("=" * 70)
    print(f"  • Provider:               {summary['provider']}")
    print(f"  • Master Model:           {summary['model']}")
    print(f"  • Long Context Model:     {summary['long_context_model']}")
    print(f"  • Filter Model:           {summary['filter_model']}")
    print(f"  • Vision Model:           {summary['vision_model']}")
    print(f"  • Base URL:               {summary['base_url']}")
    print(f"  • Chat Completions URL:   {summary['chat_completions_url']}")
    print(f"  • Max Output Tokens:      {summary['max_output_tokens']}")
    print(f"  • Context Length:         {summary['context_length_tokens']} tokens")
    print(f"  • Key Count:              {summary['key_count']} key(s) configured")
    if summary['keys_preview']:
        print(f"  • Key Preview:            {', '.join(summary['keys_preview'])}")
    else:
        print("  • Key Preview:            [NO KEYS FOUND IN ENV]")
    print("=" * 70)
    print("Supported Providers:")
    for key, p in llm_config.PROVIDER_PRESETS.items():
        current_mark = " (ACTIVE)" if key == summary['provider'] else ""
        print(f"  - {key:16} : {p['name']} -> default: {p['default_model']}{current_mark}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Unified LLM Management CLI")
    parser.add_argument("--show", action="store_true", help="Display current LLM configuration")
    parser.add_argument("--json", action="store_true", help="Output configuration as JSON")
    parser.add_argument("--model", type=str, help="Set master LLM model across all scripts")
    parser.add_argument("--long-context-model", type=str, help="Set long-context fallback model")
    parser.add_argument("--filter-model", type=str, help="Set fast filter/ranking model")
    parser.add_argument("--provider", type=str, choices=list(llm_config.PROVIDER_PRESETS.keys()), help="Set provider preset")
    parser.add_argument("--base-url", "--url", "--endpoint", dest="base_url", type=str, help="Set custom OpenAI-compatible base URL")
    parser.add_argument("--keys", "--api-keys", "--api-key", dest="keys", type=str, help="Set API keys (comma-separated)")
    parser.add_argument("--no-save", action="store_true", help="Do not write changes to .env file (memory-only)")

    args = parser.parse_args()

    if args.json:
        print(json.dumps(llm_config.get_config_summary(), indent=2))
        return 0

    updates: dict[str, str] = {}
    if args.provider:
        preset = llm_config.PROVIDER_PRESETS.get(args.provider, {})
        if preset.get("disabled"):
            print(f"⚠️  WARNING: Provider '{args.provider}' is marked as DISABLED / SCRAPPED.")
            print(f"    Reason: {preset.get('disabled_reason', '')}\n")
        updates["LLM_PROVIDER"] = args.provider
        base_url = args.base_url or preset.get("base_url", "")
        if base_url:
            updates["LLM_BASE_URL"] = base_url
            updates["GENERAL_COMPUTE_BASE_URL"] = base_url
            updates["AEROLINK_BASE_URL"] = base_url
            updates["HCN_SEC_BASE_URL"] = base_url
            updates["OPENAI_API_BASE"] = base_url
        if not args.model and "default_model" in preset:
            updates["LLM_MODEL"] = preset["default_model"]
            updates["GENERAL_COMPUTE_MODEL"] = preset["default_model"]
            updates["AEROLINK_MODEL"] = preset["default_model"]
            updates["HCN_SEC_MODEL"] = preset["default_model"]
            updates["FILTER_MODEL"] = preset["default_model"]

    if args.model:
        updates["LLM_MODEL"] = args.model
        # Keep legacy aliases in sync so external CLIs reading those also pick it up
        updates["GENERAL_COMPUTE_MODEL"] = args.model
        updates["AEROLINK_MODEL"] = args.model
        updates["HCN_SEC_MODEL"] = args.model
        updates["FILTER_MODEL"] = args.model
        updates["AI_MODEL"] = args.model
        updates["RAG_MODEL"] = args.model
        updates["RESEARCH_AGENT_MODEL"] = args.model
        updates["OPENAI_MODEL"] = args.model

    if args.long_context_model:
        updates["LLM_LONG_CONTEXT_MODEL"] = args.long_context_model
        updates["GENERAL_COMPUTE_LONG_CONTEXT_MODEL"] = args.long_context_model

    if args.filter_model:
        updates["LLM_FILTER_MODEL"] = args.filter_model
        updates["FILTER_MODEL"] = args.filter_model

    if args.base_url:
        updates["LLM_BASE_URL"] = args.base_url
        updates["GENERAL_COMPUTE_BASE_URL"] = args.base_url
        updates["AEROLINK_BASE_URL"] = args.base_url
        updates["HCN_SEC_BASE_URL"] = args.base_url
        updates["OPENAI_API_BASE"] = args.base_url

    if args.keys:
        updates["LLM_API_KEYS"] = args.keys
        updates["GENERAL_COMPUTE_API_KEYS"] = args.keys
        updates["AEROLINK_API_KEYS"] = args.keys
        updates["HCN_SEC_API_KEYS"] = args.keys
        updates["JUSTWOKER_API_KEY"] = args.keys.split(",")[0]

    if updates:
        if not args.no_save:
            env_file = llm_config.update_env_file(updates)
            print(f"✅ Updated configuration in {env_file}:")
        else:
            for k, v in updates.items():
                llm_config.os.environ[k] = v
            print("✅ Applied in-memory configuration (not saved to .env):")

        for k, v in updates.items():
            print(f"   {k} = {v}")
        print()

    print_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
