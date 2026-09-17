"""pdf_to_md.py — convert PDFs to Markdown with pymupdf4llm.

Replaces heavier per-page deep-learning extraction pipelines (Docling, etc.)
with pymupdf4llm, which is built on PyMuPDF's C engine plus a lightweight
ONNX-based layout model and selective automatic OCR. Target: macOS, 16GB RAM,
no PyTorch.

Known trade-offs (intentional, not silently worked around):
- Tables with merged cells or complex financial-report / journal-typesetting
  layouts may not extract perfectly. This is an accepted accuracy gap vs.
  heavier tools for now.
- pymupdf4llm (via PyMuPDF) is AGPL-3.0 licensed. Fine for internal tooling;
  flag for review if this code ships inside a distributed or commercially
  hosted product.

OCR fallback triggers automatically on pages with no/garbled text, but needs
Tesseract on PATH. We warn at startup if it's missing rather than failing
silently on scanned pages.

Usage::

    python3 pdf_to_md.py input.pdf
    python3 pdf_to_md.py ./papers -o ./markdown_out --recursive --workers 4
    python3 pdf_to_md.py ./papers --skip-existing -v
    python3 pdf_to_md.py ./papers --force-ocr   # opt back into OCR if needed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

try:
    import pymupdf4llm
except ImportError:  # pragma: no cover - dependency guard
    sys.exit("pymupdf4llm is not installed. Run: pip install pymupdf4llm")

try:
    from tqdm import tqdm
except ImportError:  # tqdm is optional; fall back to plain prints
    tqdm = None


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def convert_one(pdf_path: str, output_path: str, force_ocr: bool = False,
                verbose: bool = False, write_images: bool = False) -> float:
    """Convert a single PDF to Markdown. Returns wall time in seconds.

    OCR is disabled by default (use_ocr=False) since we only need embedded
    text — this avoids the garbled-figure OCR seen on figure-heavy papers and
    removes the Tesseract dependency. Pass force_ocr=True to opt back in.

    Raises on failure (caller decides how to handle per-file).
    """
    t0 = time.monotonic()
    md_text = pymupdf4llm.to_markdown(
        pdf_path,
        use_ocr=force_ocr,
        force_ocr=force_ocr,
        write_images=write_images,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md_text, encoding="utf-8")
    dt = time.monotonic() - t0
    if verbose:
        print(f"  ✓ {Path(pdf_path).name} -> {out.name} ({dt:.1f}s, "
              f"{len(md_text)} chars)")
    return dt


def _worker(args: tuple) -> tuple[str, Optional[str], float]:
    """Top-level worker for ProcessPoolExecutor (must be picklable)."""
    pdf_path, output_path, force_ocr, verbose, write_images = args
    try:
        dt = convert_one(pdf_path, output_path, force_ocr=force_ocr,
                         verbose=verbose, write_images=write_images)
        return (pdf_path, None, dt)
    except Exception as e:  # one bad PDF must not kill the batch
        return (pdf_path, f"{type(e).__name__}: {e}", 0.0)


def _collect_pdfs(input_path: Path, recursive: bool) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise SystemExit(f"Input file is not a PDF: {input_path}")
        return [input_path]
    if input_path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        return sorted(input_path.glob(pattern))
    raise SystemExit(f"Input not found: {input_path}")


def _output_path_for(pdf_path: Path, input_root: Path, output_dir: Path,
                     recursive: bool) -> Path:
    """Mirror relative subdirectory structure when run recursively."""
    if recursive and pdf_path.parent != input_root:
        rel = pdf_path.parent.relative_to(input_root)
        return output_dir / rel / f"{pdf_path.stem}.md"
    return output_dir / f"{pdf_path.stem}.md"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert PDF(s) to Markdown using pymupdf4llm.")
    parser.add_argument("input", help="PDF file or directory of PDFs")
    parser.add_argument("-o", "--output", default="./markdown_out",
                        help="Output directory (default: ./markdown_out)")
    parser.add_argument("-w", "--workers", type=int,
                        default=min(4, os.cpu_count() or 1),
                        help="Parallel worker processes (default: min(4, cpu_count))")
    parser.add_argument("--recursive", action="store_true",
                        help="Recurse into subdirectories")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip PDFs whose .md output already exists")
    parser.add_argument("--force-ocr", action="store_true",
                        help="Opt in to OCR (off by default; we only need text)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="More detailed logging")
    args = parser.parse_args(argv)

    if not _tesseract_available():
        print("WARNING: Tesseract not found on PATH. Scanned/imaging-only pages "
              "will come back with little or no text instead of erroring. "
              "Install with: brew install tesseract", file=sys.stderr)

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    pdfs = _collect_pdfs(input_path, args.recursive)
    if not pdfs:
        print(f"No PDFs found under {input_path}"
              f"{' (recursive)' if args.recursive else ''}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    skipped = 0
    for pdf in pdfs:
        out = _output_path_for(pdf, input_path if input_path.is_dir() else pdf.parent,
                               output_dir, args.recursive and input_path.is_dir())
        if args.skip_existing and out.exists():
            skipped += 1
            if args.verbose:
                print(f"  - skip (exists): {out.name}")
            continue
        jobs.append((str(pdf), str(out), args.force_ocr, args.verbose, False))

    print(f"Converting {len(jobs)} PDF(s) with {args.workers} worker(s) "
          f"-> {output_dir}")
    if skipped:
        print(f"Skipped {skipped} existing output file(s).")

    results: list[tuple[str, Optional[str], float]] = []
    start = time.monotonic()

    if tqdm is not None:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(_worker, j): j for j in jobs}
            for fut in tqdm(as_completed(futures), total=len(jobs),
                            desc="PDFs", unit="pdf"):
                results.append(fut.result())
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = [ex.submit(_worker, j) for j in jobs]
            for fut in futures:
                res = fut.result()
                results.append(res)
                if not res[1] and args.verbose:
                    pass  # convert_one already printed on success

    wall = time.monotonic() - start
    succeeded = [r for r in results if r[1] is None]
    failed = [r for r in results if r[1] is not None]
    avg = (sum(r[2] for r in succeeded) / len(succeeded)) if succeeded else 0.0

    print("\n" + "=" * 50)
    print(" PDF -> MARKDOWN SUMMARY")
    print("=" * 50)
    print(f" Total submitted : {len(jobs)}")
    print(f" Succeeded       : {len(succeeded)}")
    print(f" Failed          : {len(failed)}")
    if skipped:
        print(f" Skipped (exist) : {skipped}")
    print(f" Wall time       : {wall:.1f}s")
    if succeeded:
        print(f" Avg time/file   : {avg:.2f}s")
    if failed:
        print("\nFailures:")
        for pdf_path, err, _ in failed:
            print(f"  - {Path(pdf_path).name}: {err}")
    print("=" * 50)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
