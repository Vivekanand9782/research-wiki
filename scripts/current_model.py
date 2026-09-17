#!/usr/bin/env python3
"""Print the active Research Wiki General Compute model."""

import argparse
import json
import os
import sys
from pathlib import Path


def get_model() -> dict[str, str]:
    """Return the configured General Compute model and its source."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import config

        model = getattr(config, "GENERAL_COMPUTE_MODEL", None) or getattr(
            config, "AI_MODEL", None
        )
        if model:
            return {"model": model, "source": "config"}
    except Exception:
        pass

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        import llm_config
        return {"model": llm_config.get_model(), "source": "llm_config"}
    except Exception:
        pass

    env_model = os.environ.get("LLM_MODEL") or os.environ.get("GENERAL_COMPUTE_MODEL")
    if env_model:
        return {"model": env_model, "source": "env"}
    return {"model": "claude-opus-5-thinking", "source": "fallback"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    result = get_model()
    print(json.dumps(result) if args.json else result["model"])


if __name__ == "__main__":
    main()
