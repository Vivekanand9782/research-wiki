import os
import datetime
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None  # PyMuPDF
from pathlib import Path
import json
import hashlib
import numpy as np
import shutil
import re
import os
import tempfile
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from genai_client import get_ai_response, generate_content_with_retry
import config
from pipeline_logger import PipelineLogger


# Locks are process-wide because multiple extractor instances can coexist in
# batch drivers and tests. Instance-local locks do not protect shared wiki files.
_PROCESS_INDEX_LOCK = threading.Lock()
_PROCESS_NODE_LOCKS: Dict[str, threading.Lock] = defaultdict(threading.Lock)
_PROCESS_NODE_LOCKS_GUARD = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Safety helpers — keep the wiki self-protecting against the failure modes we
# inventoried in this session:
#   1. Schema drift: page content that doesn't satisfy the seed-page schema
#      should never land on disk.
#   2. Silent LLM failures: responses that contain failure-text patterns
#      ("AI Error: ...", "I cannot ...", empty body) but did not raise an
#      exception should be treated as failures.
#   3. Operational hygiene: every paper run gets a per-paper post-ingest
#      lint pass, and config is validated at startup so a typo in
#      ``config.AI_MODEL`` doesn't silently fall back to another model.
#
# These helpers are intentionally pure functions (no I/O) so they're easy to
# unit-test from ``tests/test_pdf_extractor.py``.
# ─────────────────────────────────────────────────────────────────────────────

# Patterns whose presence at the start of an LLM response indicates failure
# even though no exception was raised. The first match wins. Anchored to the
# beginning of the (stripped) response so legitimate prose mentioning these
# words elsewhere does not trip the check.
_LLM_FAILURE_PATTERNS = [
    re.compile(r"^\s*AI Error\b", re.IGNORECASE),
    re.compile(r"^\s*Error:\s", re.IGNORECASE),
    re.compile(r"^\s*\[Errno\s+\d+\]"),
    re.compile(r"^\s*Sorry[,\.]", re.IGNORECASE),
    re.compile(r"^\s*I'?m sorry", re.IGNORECASE),
    re.compile(r"^\s*I (cannot|can't|am unable|do not|don't have)", re.IGNORECASE),
    re.compile(r"^\s*As an? (AI|language model)", re.IGNORECASE),
]


def is_llm_failure_text(text: str | None) -> bool:
    """Return True if ``text`` looks like a failed LLM response.

    Catches three flavours that ``raise_on_error=True`` won't catch:
      * empty / whitespace-only responses
      * "AI Error: ..." or "[Errno N] ..." strings that the genai_client
        sometimes returns on transport-level failures it failed to raise on
      * refusal patterns ("I cannot ...", "I'm sorry, ...", "As an AI ...")

    The check is *anchored* to the start of the response so prose that
    happens to use these words later in a longer message is not flagged.
    """
    if text is None:
        return True
    if not text.strip():
        return True
    head = text.lstrip()[:200]
    return any(p.search(head) for p in _LLM_FAILURE_PATTERNS)


_CODE_FENCE_RE = re.compile(
    r"^```(?:markdown|yaml|md)?\n?(.*?)\n?```\s*$",
    re.DOTALL,
)


def _strip_code_fence(text: str) -> str:
    """Remove ``` ... ``` or ```markdown ... ``` wrapping from an LLM response.

    The model occasionally wraps its entire Markdown output in a fenced code
    block despite explicit prompt instructions not to.  This strips the fence
    while preserving the inner content exactly.
    """
    text = text.strip()
    m = _CODE_FENCE_RE.match(text)
    if m:
        return m.group(1).strip()
    # Partial: only leading fence
    for prefix in ("```markdown\n", "```yaml\n", "```md\n", "```\n"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    # Partial: only trailing fence
    if text.endswith("\n```"):
        text = text[:-4]
    elif text.endswith("```"):
        text = text[:-3]
    return text.strip()


# Regex to extract the outermost JSON object from prose that wraps it.
_JSON_OBJECT_RE = re.compile(r'\{.*\}', re.DOTALL)


def _unwrap_schema(payload: Any) -> Any:
    """Helper to unwrap LLM outputs that regurgitate the JSON Schema structure."""
    if isinstance(payload, dict) and payload.get("type") == "object" and "properties" in payload:
        return {k: _unwrap_schema(v) for k, v in payload["properties"].items()}
    return payload


def _parse_chunk_json(text: str) -> dict:
    """Parse JSON from a chunk-summary LLM response with multiple fallbacks.

    Models sometimes return:
      - Valid JSON                              → strategy 1
      - Python dict literals (single quotes)    → strategy 2 (ast.literal_eval)
      - JSON with trailing commas               → strategy 3
      - JSON embedded in prose or markdown       → strategy 4 (regex extract)
    """
    import json as _json
    import ast as _ast

    # Strategy 1: direct JSON parse
    try:
        return _unwrap_schema(_json.loads(text))
    except _json.JSONDecodeError:
        pass

    # Strategy 1.5: parse exactly one JSON object ignoring trailing text (using raw_decode)
    first_brace = text.find("{")
    if first_brace != -1:
        try:
            obj, _ = _json.JSONDecoder().raw_decode(text[first_brace:])
            if isinstance(obj, dict):
                return _unwrap_schema(obj)
        except Exception:
            pass

    # Strategy 2: Python dict literal (single quotes, True/False/None)
    try:
        result = _ast.literal_eval(text)
        if isinstance(result, dict):
            return result
    except Exception:
        pass

    # Strategy 3: strip trailing commas before } or ]
    try:
        fixed = re.sub(r',\s*([}\]])', r'\1', text)
        return _json.loads(fixed)
    except _json.JSONDecodeError:
        pass

    # Strategy 3.5: fix JavaScript-style unquoted keys (e.g. heading: "...")
    try:
        # Regex to find unquoted keys before a colon (basic approach for standard keys)
        fixed_keys = re.sub(r'([a-zA-Z0-9_]+)\s*:', r'"\1":', text)
        return _json.loads(fixed_keys)
    except _json.JSONDecodeError:
        pass

    # Strategy 4: extract first {...} block from surrounding prose
    m = _JSON_OBJECT_RE.search(text)
    if m:
        candidate = m.group(0)
        try:
            return _json.loads(candidate)
        except _json.JSONDecodeError:
            pass
        # Try ast on extracted block too
        try:
            result = _ast.literal_eval(candidate)
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    raise ValueError(f"Could not parse JSON from LLM response ({len(text)} chars)")

# Working models preset and dynamic active model from unified config.
_SUPPORTED_GENERAL_COMPUTE_MODELS = frozenset(
    {"claude-opus-5-thinking", "gpt-oss-120b", "minimax-m2.7", getattr(config, "GENERAL_COMPUTE_MODEL", "claude-opus-5-thinking"), getattr(config, "AI_MODEL", "claude-opus-5-thinking")}
)


def validate_ai_model_name(model_name: str | None) -> tuple[bool, str]:
    """Return whether a model is in the working General Compute allowlist."""
    if not model_name:
        return False, "AI_MODEL is empty or missing"
    if (
        model_name in _SUPPORTED_GENERAL_COMPUTE_MODELS
        or model_name == getattr(config, "GENERAL_COMPUTE_MODEL", None)
        or model_name == getattr(config, "AI_MODEL", None)
    ):
        return True, "ok"
    supported = ", ".join(sorted(_SUPPORTED_GENERAL_COMPUTE_MODELS))
    return False, (
        f"AI_MODEL='{model_name}' is not supported by General Compute "
        f"(supported: {supported})."
    )


# Sections every freshly-rendered seed page must contain. Mirrors lint_wiki's
# REQUIRED_SECTIONS, kept here too so pdf_extractor doesn't depend on the
# linter at import time.
_SEED_REQUIRED_SECTIONS = (
    "**Summary**:",
    "**Sources**:",
    "**Last updated**:",
    "## Related pages",
)


def validate_seed_page_content(content: str) -> list[str]:
    """Cheap structural validation that runs on every seed page before write.

    Returns a list of human-readable problems; empty list means the content
    is good to write to disk. We deliberately mirror the linter's seed
    schema (frontmatter present, four labelled sections, no ``## Sources``
    heading) so output and lint agree.
    """
    errors: list[str] = []
    if not content.startswith("---"):
        errors.append("missing or unclosed YAML frontmatter")
    elif content.find("\n---", 3) < 0:
        errors.append("missing or unclosed YAML frontmatter")
    for s in _SEED_REQUIRED_SECTIONS:
        if s not in content:
            errors.append(f"missing required section '{s}'")
    if re.search(r"^\s*##\s+Sources\s*$", content, re.MULTILINE):
        errors.append(
            "contains forbidden '## Sources' heading "
            "(use '**Sources**:' label instead)"
        )
    return errors


class ResearchPaperExtractor:
    def __init__(self, pdf_folder: str = "../data", output_folder: str = "wiki/sources", text_folder: str = "raw/papers"):
        self.base_dir = Path(__file__).parent
        self.pdf_folder = self.base_dir / pdf_folder
        self.output_folder = self.base_dir / output_folder
        self.text_folder = self.base_dir / text_folder
        self.logger = PipelineLogger(str(self.output_folder))

        # Create base directories
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_folder.mkdir(parents=True, exist_ok=True)
        self.text_folder.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "wiki").mkdir(parents=True, exist_ok=True)

        # ── Concurrency primitives for Phase 2 parallelism ───────────────────────
        # `_index_lock` serializes appends to wiki/log.md and wiki/index.md so that
        # multiple paper-threads don't interleave their lines.
        # `_node_locks` provides one lock per concept/entity seed-page path so that
        # two papers touching the same shared page (e.g. wiki/concepts/lignin.md)
        # don't race on read-modify-write. The locks themselves are created lazily
        # under `_node_locks_guard`.
        self._index_lock = _PROCESS_INDEX_LOCK
        # Print/log statements from many threads can interleave mid-line; guard them
        # so the console stays readable.
        self._print_lock = threading.Lock()

        # Load gene registry
        gene_registry_path = self.base_dir / "wiki/entities/gene_registry.md"
        self.gene_registry_text = gene_registry_path.read_text(encoding="utf-8") if gene_registry_path.exists() else ""

    def _get_node_lock(self, file_path: Path) -> threading.Lock:
        """Return (creating if needed) the lock that guards a single seed-page file."""
        key = str(file_path.expanduser().resolve())
        with _PROCESS_NODE_LOCKS_GUARD:
            return _PROCESS_NODE_LOCKS[key]

    def _safe_print(self, msg: str):
        """Thread-safe print so multi-worker output doesn't interleave mid-line."""
        with self._print_lock:
            print(msg)

    # ── Ingest-time safety helpers ────────────────────────────────────────
    # These wrap LLM responses + file writes to enforce the invariants we
    # learnt the hard way during the May 2026 cleanup session. See the
    # module-level docstring of safety helpers for the failure modes.

    def _seed_model(self) -> str:
        """Return the General Compute model used for seed-page generation."""
        return config.FILTER_MODEL

    def _safe_llm_text(self, prompt: str, *, model: str) -> str:
        """Call the LLM and refuse to return failure-text responses.

        Exists because ``get_ai_response(..., raise_on_error=True)`` raises
        only on transport-level failures. The genai_client occasionally
        returns a 200 with body ``"AI Error: ..."`` or a refusal pattern
        ("I'm sorry, I cannot..."). We detect those and raise ourselves so
        the caller skips the write.
        """
        # thinking=False: seed-page snippets are short factual prose; Qwen3.6
        # "nothink" mode keeps them fast and token-cheap.
        raw = get_ai_response(prompt, model=model, raise_on_error=True, thinking=False)
        text = (raw or "").strip()
        # Strip stray code fences here too; the per-call sites also strip
        # but doing it once centrally means the failure check below sees
        # the actual content.
        text = re.sub(r"^```(?:markdown|text|yaml)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text).strip()
        if is_llm_failure_text(text):
            raise RuntimeError(
                "LLM returned a failure-pattern response: "
                f"{text[:200]!r}"
            )
        return text

    def _ingest_backup_dir(self) -> Path:
        """Per-process backup directory used when the ingest pipeline modifies
        existing seed pages. Lazily created the first time it's needed."""
        if not hasattr(self, "_ingest_backup_dir_cached"):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._ingest_backup_dir_cached = (
                self.base_dir / ".backup" / f"ingest_session_{ts}"
            )
        return self._ingest_backup_dir_cached

    def _backup_before_modify(self, file_path: Path) -> None:
        """Copy ``file_path`` to a per-session backup tree before in-place
        edits. Silent no-op if the file does not exist."""
        if not file_path.exists():
            return
        try:
            rel = file_path.relative_to(self.base_dir)
        except ValueError:
            rel = Path(file_path.name)
        dest = self._ingest_backup_dir() / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(file_path, dest)
        except OSError as e:
            self._safe_print(f"  ├─ ⚠️  backup of {rel} failed: {e}")

    def _safe_write_seed_page(self, file_path: Path, content: str,
                              *, name: str, category: str,
                              modify: bool) -> bool:
        """Atomic-ish write of a seed page, gated by structural validation.

        Returns True on write, False if we refused to write because the
        content failed validation. ``modify=True`` triggers a backup of the
        existing file before overwriting.
        """
        errs = validate_seed_page_content(content)
        if errs:
            self._safe_print(
                f"  ├─ ⚠️  refusing to write {category} '{name}' — "
                f"validation failed: {errs}"
            )
            return False
        if modify:
            self._backup_before_modify(file_path)
        # Use a unique sibling temp file so independent processes cannot
        # clobber one shared ``.tmp`` path. ``os.replace`` is atomic in-place.
        tmp_path = None
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=str(file_path.parent),
                prefix=f".{file_path.name}.", suffix=".tmp", delete=False,
            ) as tmp:
                tmp.write(content)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = Path(tmp.name)
            os.replace(tmp_path, file_path)
            tmp_path = None
        except OSError as e:
            self._safe_print(f"  ├─ ⚠️  write failed for {file_path}: {e}")
            return False
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        # Track touched files for the post-ingest lint pass.
        if not hasattr(self, "_touched_files"):
            self._touched_files: set[Path] = set()
        self._touched_files.add(file_path)
        # Run-level accumulator (NOT reset per paper) so the ingest pipeline can
        # roll up exactly the seed pages this run modified.
        if not hasattr(self, "_run_touched_files"):
            self._run_touched_files: set[Path] = set()
        self._run_touched_files.add(file_path)
        return True

    def _verify_changed_pages(self, paper_name: str) -> None:
        """Quick lint of files we touched during this paper's ingest.

        Called at the end of ``populate_wiki_nodes``. Reports any seed pages
        whose final content fails ``validate_seed_page_content`` — usually
        zero, but if it ever fires, the message points straight at the
        offending file and the failure mode.
        """
        touched = getattr(self, "_touched_files", set())
        if not touched:
            return
        bad: list[tuple[Path, list[str]]] = []
        for f in list(touched):
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            errs = validate_seed_page_content(text)
            if errs:
                bad.append((f, errs))
        if bad:
            self._safe_print(
                f"  └─ ⚠️  post-ingest lint found {len(bad)} file(s) with issues "
                f"after ingesting {paper_name}:"
            )
            for f, errs in bad:
                self._safe_print(f"      {f.relative_to(self.base_dir)}: {errs}")
        else:
            self._safe_print(
                f"  └─ post-ingest lint clean: {len(touched)} files, 0 issues"
            )
        # Reset for the next paper.
        self._touched_files = set()

    @staticmethod
    def _validate_runtime_config() -> None:
        """Warn at startup when configured model names look invalid."""
        for attr in ("AI_MODEL", "FILTER_MODEL"):
            val = getattr(config, attr, None)
            ok, reason = validate_ai_model_name(val)
            if not ok:
                print(f"⚠️  config.{attr}: {reason}")

    def _load_pdf_part(self, pdf_path: Path) -> dict:
        """Read PDF bytes as General Compute-compatible inline data."""
        with open(pdf_path, 'rb') as f:
            data = f.read()
        return {"inline_data": {"mime_type": "application/pdf", "data": data}}

    def _truncate_for_context(self, full_raw_text: str) -> str:
        """Hard-truncate to 35,000 characters to fit within the proxy's request size limit (~43k chars total prompt).

        This is NOT chunking or summarization — it simply caps very long documents so we don't
        exceed the proxy's input payload limits which trigger WAF blocks (HTTP 451).
        """
        return full_raw_text[:35000]

    def chunk_and_summarize(self, full_raw_text: str) -> str:
        """Deprecated alias kept for backward compatibility — see _truncate_for_context."""
        return self._truncate_for_context(full_raw_text)

    def generate_paper_summary(
        self, full_text: str, pdf_name: str, extracted_doi: str = None,
        *,
        api_metadata: dict | None = None,
        gene_registry_text: str = "",
        tables: list | None = None,
        equations: list | None = None,
        source_was_truncated: bool = False,
        original_text_len: int = 0,
    ) -> str:
        """Process the raw text using AI to create a structured Markdown summary for the wiki.

        The prompt is built by ``prompts.build_main_prompt`` (Tasks 3 + 6
        of the ingestion-prompt overhaul). The builder injects
        ``extracted_doi``, lists the table captions and equation IDs from
        the slim sidecar JSON, and emits a truncation warning when the
        source markdown exceeded ``TRUNCATION_THRESHOLD_CHARS`` before
        truncation. All keyword arguments are optional — the prompt
        collapses cleanly when sidecar / truncation data is absent.
        """
        from datetime import date as _date
        from prompts import build_main_prompt
        prompt = build_main_prompt(
            full_text,
            extracted_doi=extracted_doi,
            api_metadata=api_metadata,
            gene_registry_text=gene_registry_text,
            tables=tables,
            equations=equations,
            source_was_truncated=source_was_truncated,
            original_text_len=original_text_len,
            today_iso=_date.today().isoformat(),
        )
        # Call General Compute to structure the document. Use raise_on_error=True
        # so a permanent rate-limit / quota failure here propagates to the paper-level
        # worker — it will skip persisting any wiki file, leaving the paper marked
        # "to do" so the next run retries instead of caching an "AI Error: ..." stub.
        structured_md = get_ai_response(prompt, raise_on_error=True, thinking=True).strip()

        # Strip code fences — the model sometimes wraps the entire output in
        # ```markdown ... ``` despite explicit instructions not to.
        structured_md = _strip_code_fence(structured_md)

        structured_md = self._clean_entities_section(structured_md.strip())

        footer = f"\n\n---\n**Source PDF:** `data/{pdf_name}.pdf`\n"
        structured_md += footer

        # Return string, let process_single_pdf handle saving to topic directory
        return structured_md

    def _clean_entities_section(self, summary: str) -> str:
        """Programmatically strip any bibliographic citations or paper names
        from the Important Entities section to ensure 100% compliance.
        """
        pattern = r"(## Important Entities\n+)(.+?)(?=\n##|\Z)"
        match = re.search(pattern, summary, re.DOTALL | re.IGNORECASE)
        if not match:
            return summary

        header, content = match.group(1), match.group(2)
        cleaned_lines = []
        citation_indicators = [r"et\s+al", r"\b\d{4}\b", r"et-al", r"kuwabara", r"kumagai", r"gao", r"he"]

        for line in content.splitlines():
            if not line.strip():
                cleaned_lines.append(line)
                continue
            match_link = re.search(r'\[\[(.*?)\]\]', line)
            name_to_check = match_link.group(1) if match_link else line
            should_drop = False
            for ind in citation_indicators:
                if re.search(ind, line, re.IGNORECASE):
                    should_drop = True
                    break
            if self._is_author_name(name_to_check):
                should_drop = True
            if not should_drop:
                cleaned_lines.append(line)

        cleaned_content = "\n".join(cleaned_lines)
        return summary[:match.start()] + header + cleaned_content + summary[match.end():]

    def repair_paper_summary(self, full_text: str, draft_summary: str, missing_sections: List[str], pdf_name: str, extracted_doi: str = None, api_metadata: dict | None = None, gene_registry_text: str = "") -> str:
        """Repair an incomplete summary by adding any missing required sections.

        Prompt sourced from ``prompts.build_repair_prompt`` (Task 3).
        """
        from prompts import build_repair_prompt
        prompt = build_repair_prompt(
            full_text, draft_summary, missing_sections, extracted_doi=extracted_doi, api_metadata=api_metadata, gene_registry_text=gene_registry_text,
        )
        repaired = get_ai_response(prompt, raise_on_error=True, thinking=True)
        repaired = _strip_code_fence(repaired)
        return self._clean_entities_section(repaired)

    def repair_hallucinations(self, full_text: str, draft_summary: str,
                              unverified_sentences: list[str], confidence: float) -> str:
        """Repair hallucinated sentences in a summary.

        Prompt sourced from ``prompts.build_hallucination_repair_prompt``.
        """
        from prompts import build_hallucination_repair_prompt
        prompt = build_hallucination_repair_prompt(
            full_text, draft_summary, unverified_sentences, confidence,
        )
        repaired = get_ai_response(prompt, raise_on_error=True, thinking=True)
        repaired = _strip_code_fence(repaired)
        return self._clean_entities_section(repaired)

    def _verify_hallucinations(self, structured_summary: str,
                               full_raw_text: str) -> "SentencesResult":
        """Run sentence-level hallucination check against the raw source."""
        from sentence_verifier import (
            extract_factual_sentences_from_summary,
            verify_summary_against_source,
        )
        sentences = extract_factual_sentences_from_summary(structured_summary)
        result = verify_summary_against_source(sentences, full_raw_text)
        print(f"  │  Hallucination confidence: {result.confidence:.2f} "
              f"({len(result.verified)}/{result.total} sentences verified)")
        if result.unverified:
            print(f"  │  ⚠ Unverified sentences ({len(result.unverified)}):")
            for s in result.unverified[:5]:
                print(f"  │    - {s[:100]}{'...' if len(s) > 100 else ''}")
            if len(result.unverified) > 5:
                print(f"  │    ... and {len(result.unverified) - 5} more")
        return result

    def _extract_raw_text(
        self,
        pdf_path: Path,
        pdf_part=None,
        text_path: Path | None = None,
    ) -> str:
        """Return raw markdown text for this PDF, using the cached file when present.

        Single PDF→markdown implementation for the whole pipeline: the bulk
        pre-pass in ``ingest_parallel.py`` calls this too, so there is one
        extraction path rather than two.

          1. Cached ``text_path`` if it already exists.
          2. pymupdf4llm — local, fast, free, no API keys.
          3. Datalab cloud API — per-PDF fallback only when pymupdf4llm fails
             (corrupt or unsupported PDF).

        ``pdf_part`` is accepted and ignored for backward compatibility.
        """
        if text_path is not None and text_path.exists():
            print(f"  ├─ Found existing raw text at {text_path}, skipping extraction...")
            with open(text_path, "r", encoding="utf-8") as f:
                return f.read()

        if text_path is None:
            return ""

        try:
            import pymupdf4llm
            md_text = pymupdf4llm.to_markdown(str(pdf_path), use_ocr=False)
            if md_text and len(md_text.strip()) > 100:
                text_path.parent.mkdir(parents=True, exist_ok=True)
                text_path.write_text(md_text, encoding="utf-8")
                print(f"  ├─ Extracted markdown via pymupdf4llm → {text_path}")
                return md_text
        except Exception as local_exc:
            print(f"  ├─ ⚠️  pymupdf4llm failed for {pdf_path.name}: {local_exc}; "
                  f"falling back to PyMuPDF fitz...")

        try:
            if fitz is None:
                try:
                    import pymupdf as fitz
                except ImportError:
                    import fitz
            doc = fitz.open(str(pdf_path))
            pages_md = []
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    pages_md.append(f"## Page {i + 1}\n\n{text}")
            doc.close()
            if pages_md:
                md_text = "\n\n".join(pages_md)
                text_path.parent.mkdir(parents=True, exist_ok=True)
                text_path.write_text(md_text, encoding="utf-8")
                print(f"  ├─ Extracted text via PyMuPDF fitz → {text_path}")
                return md_text
        except Exception as fitz_exc:
            print(f"  ├─ ⚠️  PyMuPDF fitz failed for {pdf_path.name}: {fitz_exc}; falling back to Datalab...")

        try:
            from datalab_extractor import convert_one
            full_raw_text = convert_one(pdf_path, text_path, mode="fast")
            if not full_raw_text:
                print("  ├─ ⚠️  Datalab returned empty markdown.")
            else:
                print(f"  ├─ Saved raw extracted text to {text_path}")
            return full_raw_text
        except Exception as e:
            print(f"  ├─ ⚠️  Datalab extraction failed for {pdf_path.name}: {e}")
            return ""

    def _run_chunked_extraction(self, full_raw_text: str) -> tuple[str, int]:
        """Map-reduce summarisation for long papers (Task 10 wiring).

        Chunks the source by H2/H3 boundaries, summarises each chunk with
        a tight LLM call, and aggregates the per-chunk JSONs into a
        single Markdown-flavoured "PRE-SUMMARISED CHUNKS" block the
        Stage A prompt can consume in place of raw text.

        Returns ``(aggregated_text, n_llm_calls)`` so the caller can
        track per-paper LLM cost.

        Resilient: if a chunk's LLM call or JSON parse fails, falls back
        to a degraded intermediate that just records the chunk's first
        500 chars as a single "key point". Lets Stage A still run with
        partial coverage rather than blowing up the whole paper.
        """
        import json as _json
        from prompts import (
            aggregate_chunk_intermediates,
            build_chunk_summary_prompt,
            chunk_by_sections,
        )

        chunks = chunk_by_sections(full_raw_text)
        intermediates: list[dict] = []
        n_calls = 0
        for heading, body in chunks:
            prompt = build_chunk_summary_prompt(heading, body)
            raw = ""
            try:
                raw = get_ai_response(prompt, raise_on_error=True, thinking=True).strip()
                n_calls += 1
                raw = _strip_code_fence(raw)
                # Also strip ```json fences specifically
                for prefix in ("```json", "```"):
                    if raw.startswith(prefix):
                        raw = re.sub(rf"^{re.escape(prefix)}\n?", "", raw, count=1)
                if raw.endswith("```"):
                    raw = re.sub(r"\n?```$", "", raw, count=1)
                cleaned = raw.strip()

                payload = _parse_chunk_json(cleaned)
                if not isinstance(payload, dict):
                    raise ValueError("non-dict chunk JSON")
                intermediates.append(payload)
            except Exception as exc:  # noqa: BLE001
                # Provider outages are batch-level failures, not malformed
                # chunks. Propagate after the client's bounded retries instead
                # of issuing one full retry sequence per remaining chunk.
                if getattr(exc, "retryable", False):
                    raise
                # Log first 200 chars of the raw LLM response for debugging
                raw_preview = (raw[:200] + '...') if len(raw) > 200 else raw
                print(f"  │  [!] chunk {heading!r} summary failed ({exc!r}); "
                      "including degraded intermediate")
                print(f"  │      raw response preview: {raw_preview!r}")
                intermediates.append({
                    "heading": heading,
                    "key_points": [body[:500].strip()],
                    "entities": [],
                    "data_points": [],
                })
        print(f"  │  chunker: {len(chunks)} chunks → {n_calls} LLM calls")
        return aggregate_chunk_intermediates(intermediates), n_calls

    def _generate_via_two_stage(
        self, full_text: str, pdf_name: str, *,
        extracted_doi: str | None = None,
        api_metadata: dict | None = None,
        gene_registry_text: str = "",
        tables: list | None = None,
        equations: list | None = None,
        source_was_truncated: bool = False,
        original_text_len: int = 0,
        paper_type: str | None = None,
        today_iso: str | None = None,
    ) -> str:
        """Two-stage extraction (Task 7 + Task 11 wiring).

        Stage A: build_stage_a_prompt → LLM JSON. Stage B: pure-Python
        renderer.render_summary_from_json (canonicalises wikilinks via
        wiki_vocabulary, renders verified evidence quotes as Markdown
        footnotes). The Stage A JSON is also persisted to
        ``raw/papers/<paper>.summary.json`` so search/RAG can index the
        structured output without re-parsing markdown.

        Lazy imports keep the legacy code path (and its test stubs) free
        of any new dependencies.
        """
        import json as _json
        from prompts import (
            DEFAULT_PAPER_TYPE,
            build_stage_a_prompt,
        )
        from renderer import render_summary_from_json

        try:
            from wiki_vocabulary import get_index as _vocab_index
            vocab = _vocab_index()
        except Exception as exc:  # noqa: BLE001 — vocabulary is best-effort
            print(f"  │  [!] Could not load wiki_vocabulary: {exc!r}; continuing without canonicalisation")
            vocab = None

        if paper_type is None:
            try:
                from paper_classifier import classify_paper_type
                # No LLM caller passed — heuristic-only classification.
                cr = classify_paper_type(full_text)
                paper_type = cr.paper_type
                print(f"  │  paper_type={paper_type} (source={cr.source})")
            except Exception:
                paper_type = DEFAULT_PAPER_TYPE

        prompt = build_stage_a_prompt(
            full_text,
            extracted_doi=extracted_doi,
            api_metadata=api_metadata,
            gene_registry_text=gene_registry_text,
            tables=tables,
            equations=equations,
            source_was_truncated=source_was_truncated,
            original_text_len=original_text_len,
            paper_type=paper_type,
            today_iso=today_iso,
        )
        # raise_on_error=True so quota failures don't get cached.
        # thinking=True: summary extraction benefits from Qwen3.6 reasoning.
        raw = get_ai_response(prompt, raise_on_error=True, thinking=True).strip()

        def _clean_and_parse(raw_text: str) -> dict:
            """Strip fences and parse the first JSON object in the response."""
            text = raw_text.strip()
            for prefix in ("```json", "```yaml", "```"):
                if text.startswith(prefix):
                    text = re.sub(rf"^{re.escape(prefix)}\n?", "", text, count=1)
            if text.endswith("```"):
                text = re.sub(r"\n?```$", "", text, count=1)
            text = text.strip()
            try:
                return _json.loads(text)
            except Exception as exc:  # noqa: BLE001
                # Fallback for models appending conversational fluff or markdown
                first_brace = text.find("{")
                if first_brace != -1:
                    try:
                        return _json.JSONDecoder().raw_decode(text[first_brace:])[0]
                    except Exception:
                        pass
                raise RuntimeError(f"Stage A JSON parse failed: {exc!r}") from exc

        try:
            payload = _clean_and_parse(raw)
        except Exception as exc:  # noqa: BLE001
            # Truncation at the model's 8K output-token cap is the usual
            # culprit for mid-JSON cuts ("Expecting ',' delimiter",
            # "Expecting property name..."). Retry once with a compact-output
            # prompt so the payload fits in a single response before
            # surrendering to the legacy single-call path.
            print("  │  [!] Stage A JSON unparseable; retrying once with compact-output limits")
            compact_raw = get_ai_response(
                build_stage_a_prompt(
                    full_text,
                    extracted_doi=extracted_doi,
                    api_metadata=api_metadata,
                    gene_registry_text=gene_registry_text,
                    tables=tables,
                    equations=equations,
                    source_was_truncated=source_was_truncated,
                    original_text_len=original_text_len,
                    paper_type=paper_type,
                    today_iso=today_iso,
                    compact_output=True,
                ),
                raise_on_error=True,
                thinking=True,
            )
            try:
                payload = _clean_and_parse(compact_raw)
            except Exception as exc2:  # noqa: BLE001
                # JSON parse failure is loud but recoverable — caller will
                # log and the legacy fallback can pick up.
                raise RuntimeError(f"Stage A JSON parse failed: {exc2!r}") from exc2

        # Unwrap if LLM regurgitated the JSON Schema envelope
        payload = _unwrap_schema(payload)

        # Persist the JSON sidecar (Task 7).
        try:
            sidecar_path = self.text_folder / f"{pdf_name}.summary.json"
            sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            sidecar_path.write_text(
                _json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  │  [!] Could not write summary.json sidecar: {exc!r}")

        result = render_summary_from_json(
            payload,
            vocab_index=vocab,
            paper_name=pdf_name,
            source_text=full_text,
            paper_type=paper_type,
        )
        if result.warnings:
            print(f"  │  renderer warnings ({len(result.warnings)}): "
                  f"{result.warnings[:3]}{'...' if len(result.warnings) > 3 else ''}")
        if result.new_candidates:
            print(f"  │  new entity candidates ({len(result.new_candidates)}): "
                  f"{result.new_candidates[:5]}{'...' if len(result.new_candidates) > 5 else ''}")

        # Paper-type-aware strict validation. A correction notice's
        # rendered output won't have all 12 sections (it has 4 by design),
        # so we tell the validator to use sections_for(paper_type).
        from genai_client import validate_structured_summary_strict
        validation = validate_structured_summary_strict(
            result.markdown, paper_type=paper_type,
        )
        if not validation.get("valid", False):
            missing = validation.get("missing_sections", [])
            raise RuntimeError(
                f"Stage B output validation failed for paper_type={paper_type!r}: {missing}"
            )

        return result.markdown

    def _generate_and_validate_summary(self, full_raw_text: str, pdf_name: str,
                                       extracted_doi: str = None,
                                       api_metadata: dict | None = None) -> str:
        """Produce the structured wiki summary with structural + hallucination validation.

        Structural validation (12-section anchored regex) retries once
        via repair.  After structural validation passes, hallucination
        verification checks every factual sentence against the raw source
        and retries independently (up to ``MAX_HALLUCINATION_REPAIR_RETRIES``
        from config).
        """
        print("  ├─ Generating structured AI summary from text...")
        from config import (
            HALLUCINATION_CONFIDENCE_THRESHOLD,
            MAX_HALLUCINATION_REPAIR_RETRIES,
        )

        max_retries = 2
        structured_summary = ""
        missing: list = []
        prompt_injection = (
            "\nCRITICAL: Do NOT use numbers, bullets, or asterisks before the required H2 "
            "`##` headings. Output them EXACTLY as `## Heading Name`."
        )
        condensed_text = self._truncate_for_context(full_raw_text)

        # Tables/equations previously came from a `<paper>_data_objects.json`
        # sidecar. That sidecar was always written as literal `{}`, so these
        # lists were always empty; the sidecar has been removed.
        tables, equations = [], []

        original_len = len(full_raw_text)
        from prompts import DEFAULT_PAPER_TYPE, TRUNCATION_THRESHOLD_CHARS
        was_truncated = original_len > TRUNCATION_THRESHOLD_CHARS
        try:
            from paper_classifier import classify_paper_type
            paper_type = classify_paper_type(full_raw_text).paper_type
        except Exception:
            paper_type = DEFAULT_PAPER_TYPE

        try:
            from genai_client import validate_structured_summary_strict as _validate
        except ImportError:
            from genai_client import validate_structured_summary as _validate

        # ── Two-stage extraction (optional) ──
        two_stage_succeeded = False
        try:
            from config import USE_TWO_STAGE_EXTRACTION as _USE_TWO_STAGE
        except Exception:
            _USE_TWO_STAGE = False
        if _USE_TWO_STAGE:
            try:
                n_llm_calls = 0
                if was_truncated:
                    print(f"  │  [{pdf_name}] long paper ({original_len:,} chars) → chunked extraction")
                    stage_a_input, n_chunk_calls = self._run_chunked_extraction(full_raw_text)
                    n_llm_calls += n_chunk_calls
                    stage_a_truncated = False
                else:
                    stage_a_input = condensed_text
                    stage_a_truncated = was_truncated

                import datetime
                today_iso = datetime.date.today().isoformat()
                structured_summary = self._generate_via_two_stage(
                    stage_a_input + prompt_injection, pdf_name,
                    extracted_doi=extracted_doi,
                    api_metadata=api_metadata,
                    gene_registry_text=getattr(self, "gene_registry_text", ""),
                    tables=tables,
                    equations=equations,
                    source_was_truncated=stage_a_truncated,
                    original_text_len=original_len,
                    paper_type=paper_type,
                    today_iso=today_iso,
                )
                n_llm_calls += 1
                print(f"  │  ✓ two-stage extraction: {n_llm_calls} LLM call(s)")
                self.logger.log_summary_validation(
                    passed=True, retry_count=0, char_count=len(structured_summary),
                )
                two_stage_succeeded = True
            except Exception as exc:  # noqa: BLE001
                # A provider/network failure has already exhausted its bounded
                # transport retries. Calling the legacy path would make the
                # same request again and double the outage load; propagate it
                # so the batch runner can defer the remaining papers.
                if getattr(exc, "retryable", False):
                    print(f"  │  [!] Two-stage extraction stopped: {exc}")
                    self.logger.log_error(f"two-stage provider failure: {exc}")
                    raise
                print(f"  │  [!] Two-stage extraction failed ({exc!r}); falling back to legacy single-call path")
                self.logger.log_error(f"two-stage failed, falling back: {exc!r}")

        # ── Legacy single-call retry loop ──
        if not two_stage_succeeded:
            for attempt in range(max_retries):
                if attempt == 0:
                    structured_summary = self.generate_paper_summary(
                        condensed_text + prompt_injection, pdf_name, extracted_doi,
                        api_metadata=api_metadata,
                        gene_registry_text=getattr(self, "gene_registry_text", ""),
                        tables=tables, equations=equations,
                        source_was_truncated=was_truncated,
                        original_text_len=original_len,
                    )
                else:
                    structured_summary = self.repair_paper_summary(
                        condensed_text + prompt_injection, structured_summary, missing,
                        pdf_name, extracted_doi,
                        api_metadata=api_metadata,
                        gene_registry_text=getattr(self, "gene_registry_text", ""),
                    )

                validation = _validate(structured_summary, paper_type=paper_type)
                if validation.get("valid", False):
                    print(f"  │  ✓ Passed structural validation on attempt {attempt + 1}")
                    self.logger.log_summary_validation(
                        passed=True, retry_count=attempt, char_count=len(structured_summary)
                    )
                    break

                missing = validation.get("missing_sections", [])
                if attempt < max_retries - 1:
                    print(f"  │  [*] Summary missing sections on attempt {attempt + 1}/{max_retries}. "
                          f"Repairing: {missing}")
                else:
                    print(f"  │  [!] Summary validation failed after {max_retries} attempts. "
                          f"Missing: {missing}")
                    self.logger.log_summary_validation(
                        passed=False, retry_count=attempt, char_count=len(structured_summary)
                    )
                    self.logger.log_error(f"Summary validation failed. Missing: {missing}")
                    raise RuntimeError(
                        f"Summary validation failed after {max_retries} attempts: {missing}"
                    )

        structurally_valid_summary = structured_summary

        # ── Hallucination verification (both paths converge here) ──
        result = self._verify_hallucinations(structured_summary, full_raw_text)
        log_hallucination_check = getattr(self.logger, "log_hallucination_check", None)
        if callable(log_hallucination_check):
            log_hallucination_check(
                confidence=result.confidence,
                verified_count=len(result.verified),
                unverified_count=len(result.unverified),
                unverified_sentences=result.unverified,
                repair_attempt=0,
            )

        if result.confidence < HALLUCINATION_CONFIDENCE_THRESHOLD and result.total > 0:
            if two_stage_succeeded:
                print(f"  │  [!] Two-stage extraction: skipping LLM hallucination repair "
                      f"(verifier uses exact-substring match; confidence {result.confidence:.2f})")
            else:
                best_summary = structured_summary
                best_result = result

                for h_attempt in range(MAX_HALLUCINATION_REPAIR_RETRIES):
                    print(f"  │  [*] Hallucination repair attempt {h_attempt + 1}/{MAX_HALLUCINATION_REPAIR_RETRIES}")
                    structured_summary = self.repair_hallucinations(
                        full_raw_text, structured_summary,
                        result.unverified, result.confidence,
                    )
                    result = self._verify_hallucinations(structured_summary, full_raw_text)
                    if callable(log_hallucination_check):
                        log_hallucination_check(
                            confidence=result.confidence,
                            verified_count=len(result.verified),
                            unverified_count=len(result.unverified),
                            unverified_sentences=result.unverified,
                            repair_attempt=h_attempt + 1,
                        )

                    if result.confidence > best_result.confidence:
                        best_summary = structured_summary
                        best_result = result

                    if result.confidence >= HALLUCINATION_CONFIDENCE_THRESHOLD:
                        print(f"  │  ✓ Hallucination confidence {result.confidence:.2f} ≥ "
                              f"threshold {HALLUCINATION_CONFIDENCE_THRESHOLD}")
                        break
                else:
                    print(f"  │  [!] Hallucination repair did not reach threshold. "
                          f"Using best attempt (confidence: {best_result.confidence:.2f})")

                structured_summary = best_summary

        final_validation = _validate(structured_summary, paper_type=paper_type)
        if not final_validation.get("valid", False):
            missing = final_validation.get("missing_sections", [])
            self.logger.log_error(
                f"Hallucination repair output failed structural validation; "
                f"restored pre-repair summary. Missing: {missing}"
            )
            structured_summary = structurally_valid_summary

        return structured_summary

    def process_single_pdf(self, pdf_path: Path, topic_folder: str, generate_rag: bool = False, skip_summary: bool = False, skip_pageindex: bool = False):
        """Complete extraction pipeline for one PDF into topic-specific directories.

        Orchestrates the extraction steps:
          1. Raw text  (pymupdf4llm, Datalab fallback)
          2. DOI extraction + OpenAlex metadata resolution
          3. Structured summary generation + validation
        Each step is independently cached, so re-runs only redo work whose sidecar is missing.
        """
        pdf_name = pdf_path.stem
        print(f"\n📄 Processing: {pdf_name} (Topic: {topic_folder})")
        self.logger.start_paper(str(pdf_path))

        topic_text_folder = self.text_folder / topic_folder
        topic_text_folder.mkdir(parents=True, exist_ok=True)
        topic_wiki_folder = self.output_folder / topic_folder
        topic_wiki_folder.mkdir(parents=True, exist_ok=True)

        extraction_method = "datalab_general_compute"

        try:
            text_path = topic_text_folder / f"{pdf_name}.md"

            # The current raw extractor consumes the PDF path directly;
            # loading the complete PDF into an ``inline_data`` byte buffer here
            # only doubled I/O and multiplied memory use by the worker count.
            full_raw_text = self._extract_raw_text(pdf_path, None, text_path)
            self.logger.current_paper["extraction_method"] = extraction_method

            # Guard: if text extraction failed (empty / trivially short), skip
            # the LLM summary phase entirely rather than burning API calls on
            # nothing or, worse, accidentally summarising another paper's text.
            # Marked ``skipped_no_text`` so the batch driver reports it as a
            # distinct skip instead of an error: these are scanned/junk PDFs
            # with no extractable text layer, not pipeline failures.
            if not full_raw_text or len(full_raw_text.strip()) < 100:
                print(f"  └─ ⚠️  Skipping {pdf_name}: raw text extraction returned "
                      f"empty or trivially short ({len(full_raw_text.strip())} chars)")
                self.logger.current_paper["extraction_method"] = "failed"
                self.logger.log_error("Raw text extraction returned empty")
                self.logger.finish_paper()
                return {
                    "source_pdf": pdf_name,
                    "pdf_path": str(pdf_path),
                    "topic_folder": topic_folder,
                    "extraction_method": "failed",
                    "skipped_no_text": True,
                }

            image_metadata = []

            # Hook: Synchronize PageIndex hierarchical tree structure
            pageindex_tree_file = None
            if not skip_pageindex:
                try:
                    from pageindex_ingest_hook import hook_pageindex_index
                    pi_res = hook_pageindex_index(pdf_path, md_path=text_path)
                    pageindex_tree_file = pi_res.get("tree_file")
                    if pageindex_tree_file:
                        self.logger.current_paper["pageindex_tree"] = pageindex_tree_file
                        print(f"  ├─ ✓ Synced PageIndex tree: {pageindex_tree_file}")
                except Exception as pi_exc:
                    print(f"  ├─ ⚠️  PageIndex hook failed for {pdf_name}: {pi_exc}")

            if not skip_summary:
                from paper_metadata import extract_doi_from_text
                extracted_doi = extract_doi_from_text(full_raw_text)

                api_metadata = None
                if extracted_doi:
                    from paper_metadata import resolve_metadata
                    print(f"  ├─ Fetching API metadata for DOI: {extracted_doi}")
                    try:
                        api_metadata = resolve_metadata(extracted_doi)
                    except Exception:
                        api_metadata = None
                    if api_metadata is None:
                        print("  ├─ ⚠️ API metadata unavailable; continuing with DOI-only metadata")

                structured_summary = self._generate_and_validate_summary(
                    full_raw_text, pdf_name, extracted_doi, api_metadata,
                )

                # Post-process: preserve original capitalization and spacing of wikilinks.
                def format_link_in_summary(match):
                    link_text = match.group(1)
                    return f"[[{link_text.strip()}]]"

                structured_summary = re.sub(r'\[\[(.*?)\]\]', format_link_in_summary, structured_summary)

                # Fix 1: Strip code fences in case LLM emitted them
                for prefix in ("```markdown\n", "```\n"):
                    if structured_summary.startswith(prefix):
                        structured_summary = structured_summary[len(prefix):]
                        break
                if structured_summary.endswith("\n```"):
                    structured_summary = structured_summary[:-4]
                elif structured_summary.endswith("```"):
                    structured_summary = structured_summary[:-3]
                structured_summary = structured_summary.strip()

                # Final defense-in-depth guard: the independent wiki linter's
                # source schema must pass before any page is overwritten.
                from lint_wiki import validate_source_page
                source_errors = validate_source_page(structured_summary)
                if source_errors:
                    raise RuntimeError(
                        f"Refusing to write malformed source page: {source_errors}"
                    )

                # Fix 5: Always output to uncategorized per spec
                uncategorized_folder = self.output_folder / "uncategorized"
                uncategorized_folder.mkdir(parents=True, exist_ok=True)
                md_path = uncategorized_folder / f"{pdf_name}.md"

                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(structured_summary)

                complete_data = {
                    "source_pdf": pdf_name,
                    "pdf_path": str(pdf_path),
                    "topic_folder": "uncategorized",

                    "extraction_method": extraction_method,
                    "ai_structured_summary": structured_summary,
                    "images": image_metadata,
                    "pageindex_tree": pageindex_tree_file,
                }

                print(f"  └─ ✓ Saved Wiki Markdown to {md_path}")

                self.populate_wiki_nodes(structured_summary, pdf_name)
                self.logger.finish_paper()
                return complete_data

            complete_data = {
                "source_pdf": pdf_name,
                "pdf_path": str(pdf_path),
                "topic_folder": topic_folder,
                "extraction_method": extraction_method,
                "images": image_metadata,
                "pageindex_tree": pageindex_tree_file,
            }
            self.logger.finish_paper()
            return complete_data

        except Exception as e:
            print(f"  └─ ❌ Error processing {pdf_path.name}: {e}")
            self.logger.log_error(str(e))
            self.logger.current_paper["extraction_method"] = "failed"
            self.logger.finish_paper()
            return {
                "source_pdf": pdf_name,
                "pdf_path": str(pdf_path),
                "extraction_method": "failed",
                "error": str(e),
                "retryable": bool(getattr(e, "retryable", False)),
            }

    def _generate_seed_page(self, name: str, category: str, paper_context: str,
                            pdf_name: str, today_iso: str) -> str:
        """Create a brand-new seed page for a concept/entity.

        Architecture: Python owns the page structure (frontmatter, **Sources**,
        **Last updated**, ## Related pages). The LLM is responsible for one
        thing only — a 1-3 sentence factual definition of `name` derived from
        `paper_context`. This eliminates an entire family of bugs:

          * the LLM cannot drop the **Sources** label or invent a duplicate
            ## Sources section;
          * the LLM cannot fill ## Related pages with the source paper or
            other forward-references;
          * the LLM cannot leak the framing phrasing ("X was mentioned in
            paper Y") into the body — the prompt no longer contains it.

        If the snippet is too thin to summarise, we emit a stub page with a
        clearly-marked TODO so the structural linter can pick it up later;
        we do NOT call the LLM in that case.
        """
        MIN_CONTEXT_CHARS = 80
        snippet = (paper_context or "").strip()

        if len(snippet) < MIN_CONTEXT_CHARS:
            summary_text = (
                f"_Stub: snippet from `[[{pdf_name}]]` was too thin to summarise "
                "deterministically. Needs human review or a richer source._"
            )
        else:
            prompt = (
                "You are writing a one-paragraph factual definition for a "
                "research wiki on plant genetics.\n\n"
                f"Page subject: a {category.lower()} named \"{name}\".\n\n"
                "Below is a snippet from a paper that mentions this "
                f"{category.lower()}. Based ONLY on the snippet, write 1-3 "
                "neutral, factual sentences defining the subject.\n\n"
                "Hard constraints:\n"
                "- Do NOT mention the paper by name. A separate Sources "
                "section will cite it.\n"
                "- Do NOT add wikilinks, headings, lists, or markdown "
                "formatting. Plain prose only.\n"
                "- Do NOT invent facts not present in the snippet.\n"
                "- If the snippet is too vague to define the subject, reply "
                "with the single token: NEEDS_HUMAN_REVIEW\n\n"
                "Snippet:\n"
                f"{snippet}\n"
            )
            try:
                raw = self._safe_llm_text(
                    prompt, model=self._seed_model(),
                )
            except Exception:
                raise

            if not raw or raw == "NEEDS_HUMAN_REVIEW":
                summary_text = (
                    f"_Stub: snippet from `[[{pdf_name}]]` could not be "
                    "summarised. Needs human review._"
                )
            else:
                # Collapse to a single paragraph; we promised plain prose.
                summary_text = re.sub(r'\s*\n\s*', ' ', raw).strip()

        return self._render_seed_page(
            name=name,
            category=category,
            summary_text=summary_text,
            sources=[pdf_name],
            today_iso=today_iso,
        )

    @staticmethod
    def _render_seed_page(name: str, category: str, summary_text: str,
                          sources: list[str], today_iso: str) -> str:
        """Deterministic schema-compliant page renderer. Always idempotent."""
        cat = category.lower()
        sources_block = "\n".join(f"- [[{s}]]" for s in sources) if sources else "- _none_"
        return (
            "---\n"
            f"tags: [{cat}]\n"
            f"type: {cat}\n"
            f"date_created: {today_iso}\n"
            f"date_updated: {today_iso}\n"
            f"source_count: {len(sources)}\n"
            "---\n"
            "\n"
            f"# {name}\n"
            "\n"
            "**Summary**:\n"
            f"{summary_text}\n"
            "\n"
            "**Sources**:\n"
            f"{sources_block}\n"
            "\n"
            f"**Last updated**: {today_iso}\n"
            "\n"
            "---\n"
            "## Related pages\n"
        )

    def _update_seed_page(self, name: str, category: str, existing_content: str,
                          new_context: str, pdf_name: str, today_iso: str) -> str:
        """Append a new finding to an existing seed page and refresh its frontmatter.

        Python performs the surgical edits; the LLM only writes the 1-3
        sentence finding text. This avoids three bugs that plagued the old
        implementation:

          * the new paper is appended to the existing **Sources**: list (not
            written as a duplicate ## Sources heading further down);
          * source_count in the frontmatter actually reflects the post-update
            value, even if the previous file was malformed;
          * the finding section is inserted before ## Related pages, never
            after, so the page's section ordering stays stable.

        If a `### Findings from [[pdf_name]]` block already appears in the
        file, the function returns the input unchanged — the caller has already
        short-circuited in that case but we double-check for safety. (A bare
        citation in **Sources** without a findings block is NOT treated as done,
        so stub citations get a real finding on re-run.)
        """
        if f"### Findings from [[{pdf_name}]]" in existing_content:
            return existing_content

        MIN_CONTEXT_CHARS = 80
        snippet = (new_context or "").strip()

        if len(snippet) < MIN_CONTEXT_CHARS:
            new_finding = (
                f"_Stub: snippet from `[[{pdf_name}]]` was too thin to "
                "summarise. Needs human review._"
            )
        else:
            prompt = (
                f"You are adding a finding to a research-wiki page about the "
                f"{category.lower()} \"{name}\".\n\n"
                "Below is a snippet from a new paper. Based ONLY on the "
                "snippet, write 1-3 neutral, factual sentences describing "
                f"what THIS paper claims about \"{name}\".\n\n"
                "Hard constraints:\n"
                "- Do NOT mention the paper by name. A separate Sources "
                "section already cites it.\n"
                "- Do NOT add wikilinks, headings, lists, or markdown "
                "formatting. Plain prose only.\n"
                "- Do NOT invent facts not present in the snippet.\n"
                "- If the snippet is too vague, reply with the single "
                "token: NEEDS_HUMAN_REVIEW\n\n"
                "Snippet:\n"
                f"{snippet}\n"
            )
            try:
                raw = self._safe_llm_text(
                    prompt, model=self._seed_model(),
                )
            except Exception:
                raise

            if not raw or raw == "NEEDS_HUMAN_REVIEW":
                new_finding = (
                    f"_Stub: snippet from `[[{pdf_name}]]` could not be "
                    "summarised. Needs human review._"
                )
            else:
                new_finding = re.sub(r'\s*\n\s*', ' ', raw).strip()

        # A thin/vague snippet yields a "_Stub: ... Needs human review_"
        # finding. Record the citation but drop the noise block (declutter).
        return self._merge_finding_into_page(
            existing_content=existing_content,
            pdf_name=pdf_name,
            finding_text=None if new_finding.startswith("_Stub:") else new_finding,
            today_iso=today_iso,
        )

    @staticmethod
    def _merge_finding_into_page(existing_content: str, pdf_name: str,
                                 finding_text: str | None, today_iso: str) -> str:
        """Surgical, idempotent merge of a new finding into an existing seed page.

        Updates frontmatter (date_updated, source_count), appends the new
        paper to the **Sources**: list (creating one if absent), and inserts
        a `### Findings from [[pdf_name]]` block immediately before the
        `## Related pages` heading (or at end of file if it's missing).
        """
        # --- 1. frontmatter -------------------------------------------------
        fm_match = re.match(r'^---\n(.*?)\n---\n', existing_content, re.DOTALL)
        if fm_match:
            yaml_block = fm_match.group(1)
            yaml_block = re.sub(
                r'date_updated:.*', f'date_updated: {today_iso}', yaml_block
            )
            count_match = re.search(r'source_count:\s*(\d+)', yaml_block)
            if count_match:
                new_count = int(count_match.group(1)) + 1
                yaml_block = re.sub(
                    r'source_count:\s*\d+',
                    f'source_count: {new_count}',
                    yaml_block,
                )
            else:
                yaml_block += "\nsource_count: 2"
            body = existing_content[fm_match.end():]
            head = f"---\n{yaml_block}\n---\n"
        else:
            head = ""
            body = existing_content

        # --- 2. **Sources**: list -------------------------------------------
        # Match the label and its bullet list (consecutive lines starting with
        # ``-``). We tolerate either a blank-line or a heading as the
        # terminator.
        sources_re = re.compile(
            r'(\*\*Sources\*\*:\s*\n)((?:\s*-\s*[^\n]*\n)+)',
        )
        s_match = sources_re.search(body)
        new_bullet = f"- [[{pdf_name}]]\n"
        if s_match:
            existing_block = s_match.group(2)
            if f"[[{pdf_name}]]" in existing_block:
                merged_block = existing_block  # already cited; idempotent
            else:
                merged_block = existing_block + new_bullet
            body = body[:s_match.start()] + s_match.group(1) + merged_block + body[s_match.end():]
        else:
            # No **Sources**: block at all — create one near the top of the body.
            # We insert it right after the first H1 heading if present, else
            # at the very start.
            h1_match = re.search(r'^#\s+[^\n]*\n', body, re.MULTILINE)
            insert_at = h1_match.end() if h1_match else 0
            sources_block = f"\n**Sources**:\n{new_bullet}\n"
            body = body[:insert_at] + sources_block + body[insert_at:]

        # --- 3. **Last updated**: line in body --------------------------
        body = re.sub(
            r'(\*\*Last updated\*\*:\s*)\S+',
            lambda m: m.group(1) + today_iso,
            body,
            count=1,
        )

        # --- 4. finding section --------------------------------------------
        # When ``finding_text`` is empty/None (e.g. the per-paper snippet was
        # too thin to summarise), record the citation in **Sources** above but
        # skip the noisy "Needs human review" findings block entirely.
        if finding_text:
            finding_section = (
                f"### Findings from [[{pdf_name}]]\n"
                f"{finding_text}\n"
                "\n"
            )
            # Match ONLY the `## Related pages` heading, not the preceding `---`
            # rule. This way the rule stays in `pre` and the finding section is
            # inserted *after* the metadata/body divider, matching the layout
            # produced by `cleanup_page` for historical pages.
            related_re = re.compile(
                r'(?:^|\n)##\s+Related\s+pages\b',
                re.IGNORECASE,
            )
            r_match = related_re.search(body)
            if r_match:
                pre = body[:r_match.start()].rstrip("\n") + "\n\n"
                post = body[r_match.start():].lstrip("\n")
                body = pre + finding_section + post
            else:
                body = (
                    body.rstrip("\n") + "\n\n" + finding_section
                    + "## Related pages\n"
                )

        return head + body

    @staticmethod
    def _is_author_name(name: str) -> bool:
        stripped = name.strip()
        # Pattern like "Last F" or "Last FM" (e.g. Xu H, DeWitt MA) or "Last, F."
        if re.match(r'^[A-Z][a-zA-Z\-]*\s+[A-Z]{1,2}$', stripped) or re.search(r',\s*[A-Z]', stripped):
            return True
        low = stripped.lower()
        author_keywords = {"teng", "kuwabara", "kumagai", "gao", "he", "shaimerdenova", "shao", "sharma", "shi", "shivashakarappa", "shorinola"}
        if any(kw in low for kw in author_keywords):
            return True
        return False

    @staticmethod
    def _node_context(name: str, summary: str) -> str:
        """Substantive prose context for an entity/concept across the summary.

        Returns the joined lines that actually DISCUSS ``name`` (lines carrying
        real prose, not just a bare ``[[wikilink]]`` list). Returns ``""`` when
        ``name`` only appears inside entity lists — the caller then skips the
        node entirely, so no seed page is created and no LLM call is spent on
        entities that carry no information in this paper.
        """
        stop = {"and", "the", "with", "for", "via", "are", "was", "that",
                "this", "from", "into", "its", "their", "also", "such",
                "these", "than", "have", "has"}
        pat = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)

        # Fallback to search without parenthetical details (e.g. "Cas9-RNP (ribonucleoprotein)" -> "Cas9-RNP")
        clean_name = re.sub(r'\s*\([^)]*\)', '', name).strip()
        pat_clean = re.compile(r'\b' + re.escape(clean_name) + r'\b', re.IGNORECASE) if clean_name and clean_name != name else None

        kept, total = [], 0
        for line in summary.splitlines():
            if not (pat.search(line) or (pat_clean and pat_clean.search(line))):
                continue
            prose = re.sub(r'\[\[.*?\]\]', '', line)  # ignore the wikilinks themselves
            words = [w for w in re.findall(r'[A-Za-z]{3,}', prose)
                     if w.lower() not in stop]
            if words:
                kept.append(line.strip())
                total += len(words)
        return ' '.join(kept)[:1200] if total >= 4 else ""

    def populate_wiki_nodes(self, structured_summary: str, pdf_name: str, node_workers: int = 4):
        """
        Parse the structured summary to extract entities and concepts.
        Generate or update 'seed pages' through General Compute.

        Optimizations vs. the original sequential version:
          1. If an existing seed page already cites `[[pdf_name]]`, the entire
             AI `_update_seed_page` call is skipped — the page is up-to-date
             for this paper.
          2. The 20-30 per-paper concept/entity calls are fanned out across
             `node_workers` threads.
          3. Each seed-page file is guarded by a per-path lock so that concurrent
             paper-threads (Phase 2 outer pool) can't race on shared concepts
             like `wiki/concepts/lignin.md`.
        """
        # Cache the date once so every page produced in this run carries the same timestamp.
        # Using date.today() (not datetime.now()) — the time-of-day component was unused.
        today_iso = datetime.date.today().isoformat()

        def extract_section(markdown: str, header: str) -> str:
            pattern = rf"(?i)##\s*{header}\s*\n(.*?)(?=\n##\s*|$)"
            match = re.search(pattern, markdown, re.DOTALL)
            return match.group(1).strip() if match else ""

        concepts_text = extract_section(structured_summary, r"Key Concepts & Theory")
        entities_text = extract_section(structured_summary, r"Important Entities")

        def _is_section_header(name: str) -> bool:
            """Return True if ``name`` looks like a section-header / category
            label that the LLM may have mis-extracted as an entity (e.g.
            ``Genes/Proteins:``, ``Tools/Techniques:``, ``Compounds/Materials``).

            Two anchors:
              1. Trailing ``:`` — a section header almost always carries a
                 colon when extracted from a list like ``**Genes/Proteins:**``.
              2. Slash-joined plural category words (no colon) — covers
                 inputs like ``Metabolites/Compounds`` that the colon rule
                 would miss.

            We never reject a name that contains a digit (genes/proteins
            usually have numbers, e.g. ``ZmMYB31``, ``OsBADH1``), nor names
            shorter than 5 chars (real abbreviations like ``ABA``,
            ``CRISPR``, etc).
            """
            if len(name) < 5:
                return False
            if any(ch.isdigit() for ch in name):
                return False
            stripped = name.strip()
            if stripped.endswith(":"):
                return True
            # Slash-joined category labels.
            CATEGORY_WORDS = {
                "compounds", "materials", "molecules", "tools", "methods",
                "products", "techniques", "genes", "proteins", "enzymes",
                "hormones", "organisms", "sources", "cultivars", "lines",
                "metabolites", "starches",
            }
            if "/" in stripped:
                parts = re.split(r"[/&]", stripped)
                # All parts must be category-like words (case-insensitive,
                # whitespace-trimmed, parenthetical content stripped).
                cleaned = []
                for p in parts:
                    p = re.sub(r"\([^)]*\)", "", p).strip().lower()
                    cleaned.append(p)
                if cleaned and all(p in CATEGORY_WORDS for p in cleaned):
                    return True
            return False

        def extract_items(text_block: str) -> dict:
            items = {}
            for line in text_block.split('\n'):
                line = line.strip()
                if not line: continue
                links = re.findall(r'\[\[(.*?)\]\]', line)
                if links:
                    for link in links:
                        if _is_section_header(link) or self._is_author_name(link):
                            continue
                        items[link] = line
                elif line.startswith('-'):
                    match = re.match(r'-\s*(?:\*\*)?([^*\n]+)(?:\*\*)?', line)
                    if match:
                        name = match.group(1).strip()
                        if name.endswith(":"):
                            name = name[:-1].strip()
                        if _is_section_header(name) or self._is_author_name(name):
                            continue
                        items[name] = line
            return items

        # Only build pages for nodes actually DISCUSSED in the summary prose.
        # Entities appearing solely in the bare "Important Entities" wikilink
        # list carry no information in this paper, so skip them entirely — no
        # seed page, no LLM call (saves cost + time). The substantive mentions
        # double as the richer context handed to the generator.
        #
        # We also require >= MIN_CONTEXT_CHARS (80) of context — the same
        # threshold the generator uses. Below it the generator can only emit a
        # "_Stub: ... too thin to summarise_" page, so gating here means thin
        # nodes are dropped outright rather than written as stub pages (and are
        # not recreated on a --force re-run).
        MIN_CONTEXT_CHARS = 80

        def _significant(names) -> dict:
            out = {}
            for name in names:
                ctx = self._node_context(name, structured_summary)
                if ctx and len(ctx) >= MIN_CONTEXT_CHARS:
                    out[name] = ctx
            return out

        concepts = _significant(extract_items(concepts_text))
        entities = _significant(extract_items(entities_text))

        # A page is "done" for this paper only once it carries a real
        # `### Findings from [[paper]]` block. Keying on the bare `[[paper]]`
        # citation instead would treat stub citations (citation in **Sources**
        # but no findings block) as done, so re-runs could never repair them.
        findings_marker = f"### Findings from [[{pdf_name}]]"

        def _strip_codefences(content: str) -> str:
            if content.startswith("```markdown"): content = content[11:]
            elif content.startswith("```yaml"): content = content[7:]
            elif content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            return content.strip()

        def _process_one_node(name: str, context: str, folder_path: Path, category: str):
            safe_name = re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()
            if not safe_name:
                return  # skip degenerate names like all-punctuation
            file_path = folder_path / f"{safe_name}.md"
            lock = self._get_node_lock(file_path)

            with lock:
                if not file_path.exists():
                    self._safe_print(f"  ├─ Generating seed page for {category}: {name}")
                    content = self._generate_seed_page(
                        name, category, context, pdf_name, today_iso
                    )
                    content = _strip_codefences(content)
                    self._safe_write_seed_page(
                        file_path, content,
                        name=name, category=category, modify=False,
                    )
                    return

                # Page already exists. Read it and decide whether an AI update
                # is actually needed. Skipping no-op updates is the single biggest
                # win for re-runs — see optimization (1) in the docstring.
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

                if findings_marker in existing_content:
                    self._safe_print(
                        f"  ├─ Already has finding from [[{pdf_name}]] — skipping {category}: {name}"
                    )
                    return

                self._safe_print(f"  ├─ Updating existing {category} page: {name}")
                content = self._update_seed_page(
                    name, category, existing_content, context, pdf_name, today_iso
                )
                content = _strip_codefences(content)
                self._safe_write_seed_page(
                    file_path, content,
                    name=name, category=category, modify=True,
                )

        def process_nodes(items: dict, folder_name: str, category: str):
            folder_path = self.base_dir / "wiki" / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

            if not items:
                return

            # node_workers <= 1 → serialize (preserves old behaviour for debugging)
            if node_workers <= 1:
                for name, context in items.items():
                    try:
                        _process_one_node(name, context, folder_path, category)
                    except Exception as e:
                        self._safe_print(f"  ├─ ⚠️  {category} '{name}' failed: {e}")
                return

            with ThreadPoolExecutor(max_workers=node_workers) as ex:
                futures = {
                    ex.submit(_process_one_node, name, context, folder_path, category): name
                    for name, context in items.items()
                }
                for fut in as_completed(futures):
                    name = futures[fut]
                    try:
                        fut.result()
                    except Exception as e:
                        self._safe_print(f"  ├─ ⚠️  {category} '{name}' failed: {e}")

        self._safe_print("  ├─ Populating Concepts and Entities...")
        process_nodes(concepts, "concepts", "Concept")
        process_nodes(entities, "entities", "Entity")
        # Post-ingest lint of just the files we touched for this paper.
        self._verify_changed_pages(pdf_name)

    def update_wiki_indexes(self, pdf_name: str, md_file_path: Path, structured_summary: str):
        """Auto-index the ingested paper in the wiki."""
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        title_match = re.search(r'## Title & Metadata\n+(.+?)(?:\n|$)', structured_summary)
        title_line = title_match.group(1).strip() if title_match else pdf_name

        tags_match = re.search(r'^tags:\s*\[(.+?)\]', structured_summary, re.MULTILINE)
        tags = tags_match.group(1).strip() if tags_match else ""

        # NOTE: When opening a file in append mode ('a'), f.tell() always reports the end of
        # file, so it is never 0 even if the file is empty. We must test existence/size BEFORE
        # opening for append, otherwise the header is only written for brand-new processes
        # whose file got created earlier in this same run.
        # The whole exists-check + append must run under a lock so concurrent paper threads
        # don't double-write the header or interleave lines.
        log_path = self.output_folder.parent / "log.md"
        index_path = self.output_folder.parent / "index.md"
        with self._index_lock:
            if not log_path.exists() or log_path.stat().st_size == 0:
                log_path.write_text("# Ingest Log\n\n", encoding="utf-8")
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"## [{current_date}] ingest | {pdf_name}\n")

            if not index_path.exists() or index_path.stat().st_size == 0:
                index_path.write_text("# Master Index\n\n", encoding="utf-8")
            with open(index_path, 'a', encoding='utf-8') as f:
                f.write(f"- [[{pdf_name}]] — {title_line} | tags: {tags} | {current_date}\n")

    def rename_pdf_if_needed(self, pdf_path: Path) -> Path:
        """Extracts title and author from the first page and renames the PDF to convention if needed."""
        # Simple check for convention: roughly matches Author_Year_Title
        if re.match(r"^[^_]+_\d{4}_[^_]+.*\.pdf$", pdf_path.name):
            return pdf_path

        print(f"\n🔄 Renaming {pdf_path.name} to convention...")
        try:
            # Extract first page text to get title and authors
            doc = fitz.open(pdf_path)
            first_page_text = doc[0].get_text()
            doc.close()

            prompt = f"""
            Analyze the following text from the first page of a scientific paper.
            Extract the primary author's last name (or first author's last name if multiple), the publication year, and a shortened, descriptive version of the title (max 6-8 words).

            Return ONLY a JSON object with this exact structure:
            {{"author": "LastName", "year": "YYYY", "title": "Short_Title_With_Underscores"}}

            Ensure the title has words separated by underscores and no special characters.
            If you cannot find the year, use "UnknownYear".
            If you cannot find the author, use "UnknownAuthor".

            Text:
            {first_page_text[:3000]}
            """

            resp = generate_content_with_retry(
                model=config.AI_MODEL,
                contents=prompt,
                thinking=False,
            )

            clean_json = resp.text.strip()
            if clean_json.startswith("```json"): clean_json = clean_json[7:-3]
            elif clean_json.startswith("```"): clean_json = clean_json[3:-3]

            metadata = json.loads(clean_json.strip())

            author = metadata.get("author", "UnknownAuthor").replace(" ", "_")
            year = metadata.get("year", "UnknownYear")
            title = metadata.get("title", "Unknown_Title").replace(" ", "_")

            # Clean up title
            title = re.sub(r'[^a-zA-Z0-9_]', '', title)

            new_name = f"{author}_{year}_{title}.pdf"
            new_path = pdf_path.parent / new_name

            # Avoid overwriting existing files
            counter = 1
            while new_path.exists() and new_path != pdf_path:
                new_name = f"{author}_{year}_{title}_{counter}.pdf"
                new_path = pdf_path.parent / new_name
                counter += 1

            if new_path != pdf_path:
                pdf_path.rename(new_path)
                print(f"  └─ Renamed to {new_name}")
                return new_path

        except Exception as e:
            print(f"  [!] Failed to auto-rename {pdf_path.name}: {e}")

        return pdf_path

    def process_all_pdfs(self, skip_summary: bool = False):
        """Process all PDFs in the folder, supporting subdirectories for topics."""
        # Sanity-check the runtime config before doing any LLM work — surfaces
        # typos in config.AI_MODEL / FILTER_MODEL early so a silent fallback
        # doesn't leave the wiki running on the wrong backend.
        self._validate_runtime_config()
        # Use rglob to recursively find PDFs in subfolders
        pdf_files = list(self.pdf_folder.rglob("*.pdf"))
        print(f"🚀 Found {len(pdf_files)} PDF files to process\n")

        all_data = []
        for pdf_path in pdf_files:
            # Determine topic folder based on its parent directory name
            if pdf_path.parent == self.pdf_folder:
                if self.pdf_folder.name == "data":
                    topic_folder = "uncategorized"
                else:
                    topic_folder = self.pdf_folder.name
            else:
                topic_folder = pdf_path.parent.name

            topic_wiki_folder = self.output_folder / topic_folder

            # Check 1: Is the original filename already processed?
            original_md_file = topic_wiki_folder / f"{pdf_path.stem}.md"
            if original_md_file.exists():
                print(f"\n⏭️  Skipping {pdf_path.name}: Already processed. Markdown found in {topic_folder}.")
                continue

            # Rename if necessary before processing
            pdf_path = self.rename_pdf_if_needed(pdf_path)
            pdf_name = pdf_path.stem

            # Check 2: After renaming, is the NEW filename already processed?
            md_file = topic_wiki_folder / f"{pdf_name}.md"

            if md_file.exists():
                print(f"\n⏭️  Skipping {pdf_name}: Already processed. Markdown found in {topic_folder}.")
            else:
                try:
                    data = self.process_single_pdf(pdf_path, topic_folder, skip_summary=skip_summary)
                    if data and data.get("extraction_method") != "failed":
                        all_data.append(data)
                        if not skip_summary and "ai_structured_summary" in data:
                            self.update_wiki_indexes(pdf_name, md_file, data["ai_structured_summary"])
                except Exception as e:
                    # Don't let one bad PDF take down the whole batch — but DO surface the
                    # error so it isn't silently swallowed.
                    print(f"❌ {pdf_path.name}: {e}")
                    try:
                        self.logger.log_error(f"{pdf_path.name}: {e}")
                    except Exception:
                        # Logger failure must never mask the original error in stdout.
                        pass

        print(f"\n✅ Processing complete!")
        self.logger.print_run_summary()
        return all_data

    def extract_all_raw(self, max_workers: int = 4):
        """Phase 1: Extract raw markdown for all PDFs (no AI).

        Delegates every PDF to :meth:`_extract_raw_text` — pymupdf4llm locally
        with a Datalab cloud fallback — so this shares one extraction
        implementation with ``ingest_parallel.py``'s bulk pre-pass instead of
        maintaining a second OpenDataLoader/JVM path. The old
        ``<paper>_data_objects.json`` sidecar is gone: it only ever carried
        tables/equations that nothing downstream consumed.

        Parameters
        ----------
        max_workers
            Number of PDFs extracted concurrently.
        """
        pdf_files = list(self.pdf_folder.rglob("*.pdf"))
        print(f"🚀 Phase 1: Extracting raw markdown from {len(pdf_files)} PDFs "
              f"(workers={max_workers})\n")

        per_pdf_plan = []
        skipped_count = 0
        for pdf_path in pdf_files:
            if pdf_path.parent == self.pdf_folder:
                topic_folder = "uncategorized" if self.pdf_folder.name == "data" else self.pdf_folder.name
            else:
                topic_folder = pdf_path.parent.name

            text_folder = self.text_folder / topic_folder
            text_folder.mkdir(parents=True, exist_ok=True)

            text_path = text_folder / f"{pdf_path.stem}.md"
            if text_path.exists():
                skipped_count += 1
                continue

            per_pdf_plan.append((pdf_path, text_path))

        print(f"📋 To process: {len(per_pdf_plan)}, Skipped: {skipped_count}\n")
        if not per_pdf_plan:
            print("✅ Nothing to do — all markdown already present.")
            return

        def _extract(item):
            pdf_path, text_path = item
            # ``_extract_raw_text`` reports and swallows its own failures, so one
            # bad PDF never aborts the run.
            md = self._extract_raw_text(pdf_path, None, text_path)
            return (pdf_path.stem, bool(md))

        ok_count = 0
        fail_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_extract, item) for item in per_pdf_plan]
            for future in as_completed(futures):
                pdf_name, success = future.result()
                if success:
                    ok_count += 1
                    print(f"✓ {pdf_name}")
                else:
                    fail_count += 1
                    print(f"✗ {pdf_name}")

        print(f"\n✅ Phase 1 complete! Processed: {ok_count}, Failed: {fail_count}, Skipped: {skipped_count}")

    def process_all_with_ai(self, max_workers: int = 4, node_workers: int = 4):
        """Phase 2: Process extracted raw data with AI (summary, entities) in parallel.

        Parameters
        ----------
        max_workers : int
            Number of papers processed concurrently. Each worker fires one
            structured-summary call plus a fan-out of seed-page calls.
        node_workers : int
            Number of concurrent concept/entity seed-page calls *within* each
            paper. Effective peak concurrency to Vertex AI is roughly
            ``max_workers * (1 + node_workers)`` so keep both modest unless
            you've raised your quota.
        """
        # Find all raw text files
        raw_files = list(self.text_folder.rglob("*.md"))
        print(
            f"🚀 Phase 2: AI processing for {len(raw_files)} papers "
            f"(workers={max_workers}, node_workers={node_workers})\n"
        )

        # Build the work list, applying the cache check up-front so the worker
        # function only has to deal with papers that actually need AI work.
        tasks = []
        skipped = 0
        for text_path in raw_files:
            pdf_name = text_path.stem
            topic_folder = text_path.parent.name
            topic_wiki_folder = self.output_folder / topic_folder
            topic_wiki_folder.mkdir(parents=True, exist_ok=True)
            md_file = topic_wiki_folder / f"{pdf_name}.md"
            if md_file.exists():
                skipped += 1
                continue
            tasks.append((text_path, pdf_name, md_file))

        print(f"📋 To process: {len(tasks)}, Skipped (already in wiki/sources): {skipped}\n")

        if not tasks:
            print("✅ Phase 2 complete! Nothing to do.")
            return

        def _process_one_paper(task):
            text_path, pdf_name, md_file = task
            try:
                self._safe_print(f"📄 AI Processing: {pdf_name}")

                with open(text_path, 'r', encoding='utf-8') as f:
                    full_raw_text = f.read()

                from paper_metadata import extract_doi_from_text
                extracted_doi = extract_doi_from_text(full_raw_text)

                self._safe_print(f"  ├─ [{pdf_name}] Generating AI summary...")
                structured_summary = self._generate_and_validate_summary(
                    full_raw_text, pdf_name, extracted_doi,
                )

                # Save wiki page first so a crash mid-populate still leaves the
                # paper marked as processed (preserves resumability).
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(structured_summary)

                # Index updates are guarded by self._index_lock inside the helper.
                self.update_wiki_indexes(pdf_name, md_file, structured_summary)

                # Concept/entity fan-out is parallel inside this paper, and each
                # seed-page write is guarded by a per-path lock for safety against
                # the outer paper-level pool.
                self.populate_wiki_nodes(
                    structured_summary, pdf_name, node_workers=node_workers
                )
                return pdf_name, True, None
            except Exception as e:
                return pdf_name, False, str(e)

        processed = 0
        failed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_process_one_paper, t): t for t in tasks}
            for future in as_completed(futures):
                pdf_name, success, error = future.result()
                if success:
                    processed += 1
                    self._safe_print(f"✅ {pdf_name}  ({processed}/{len(tasks)})")
                else:
                    failed += 1
                    self._safe_print(f"❌ {pdf_name}: {error}")

        print(
            f"\n✅ Phase 2 complete! Processed: {processed}, "
            f"Failed: {failed}, Skipped: {skipped}"
        )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto-Ingest Engine for Plant Genetics Wiki")

    base_dir = Path(__file__).parent
    parser.add_argument("--pdf-folder", type=str, default=str(base_dir / "../data"), help="Folder containing PDFs to process")
    parser.add_argument("--output-folder", type=str, default=str(base_dir / "wiki" / "sources"), help="Folder to save extracted data")
    parser.add_argument("--text-folder", type=str, default=str(base_dir / "raw" / "papers"), help="Folder to save raw extracted text")
    parser.add_argument("--skip-summary", action="store_true", help="Skip the final AI summary generation step")
    parser.add_argument(
        "--phase1-workers", type=int, default=4,
        help="Concurrent PDFs for Phase 1 (raw text/JSON extraction). Default: 4."
    )
    parser.add_argument(
        "--workers", type=int, default=4,
        help="Concurrent papers for Phase 2 (AI summary + seed pages). Default: 4."
    )
    parser.add_argument(
        "--node-workers", type=int, default=4,
        help="Concurrent concept/entity seed-page calls within each paper. Default: 4."
    )
    parser.add_argument(
        "--phase", choices=["1", "2", "both"], default="both",
        help="Run only Phase 1, only Phase 2, or both. Default: both."
    )

    args = parser.parse_args()

    extractor = ResearchPaperExtractor(
        pdf_folder=args.pdf_folder,
        output_folder=args.output_folder,
        text_folder=args.text_folder
    )

    # Phase 1: raw extraction (no AI). Phase 2: AI summary + seed pages.
    # Each phase is independently cached, so re-running resumes safely.
    if args.phase in ("1", "both"):
        extractor.extract_all_raw(max_workers=args.phase1_workers)
    if args.phase in ("2", "both"):
        extractor.process_all_with_ai(
            max_workers=args.workers,
            node_workers=args.node_workers,
        )
