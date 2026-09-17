import os
import json
import time
import threading
from datetime import datetime, timezone

class PipelineLogger:
    def __init__(self, output_folder: str):
        self.log_path = os.path.join(output_folder, "pipeline_log.jsonl")
        self._local = threading.local()
        self.run_start = time.time()
        self.total_papers = 0
        self.total_figures = 0
        self.total_errors = 0
        self.total_tokens = 0
        
        # Thread safety lock for counters and file I/O
        self._lock = threading.Lock()

        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

    @property
    def current_paper(self) -> dict:
        if not hasattr(self._local, "current_paper"):
            self._local.current_paper = {}
        return self._local.current_paper

    @current_paper.setter
    def current_paper(self, val: dict):
        self._local.current_paper = val

    @property
    def paper_start(self) -> float:
        if not hasattr(self._local, "paper_start"):
            self._local.paper_start = 0.0
        return self._local.paper_start

    @paper_start.setter
    def paper_start(self, val: float):
        self._local.paper_start = val

    def start_paper(self, pdf_path: str):
        with self._lock:
            self.current_paper = {
                "pdf_file": os.path.basename(pdf_path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "extraction_method": None,
                "page_count": None,
                "total_elements": None,
                "figures_extracted": 0,
                "figures_junk": 0,
                "figures_uncertain": 0,
                "figures_processed": 0,
                "summary_validation_passed": None,
                "summary_retry_count": 0,
                "summary_token_estimate": None,
                "hallucination_confidence": None,
                "hallucination_verified_count": 0,
                "hallucination_unverified_count": 0,
                "hallucination_repair_attempts": 0,
                "hallucination_unverified_sentences": [],
                "warnings": [],
                "errors": [],
                "processing_time_seconds": None
            }
            self.paper_start = time.time()

    def _ensure_paper_started(self):
        if not self.current_paper or "pdf_file" not in self.current_paper:
            raise RuntimeError("start_paper() must be called before logging paper-specific data.")

    def log_figures(self, junk: int, uncertain: int, processed: int):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["figures_junk"] += junk
            self.current_paper["figures_uncertain"] += uncertain
            self.current_paper["figures_processed"] += processed
            self.current_paper["figures_extracted"] += (junk + uncertain + processed)

    def log_summary_validation(self, passed: bool, retry_count: int, char_count: int):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["summary_validation_passed"] = passed
            self.current_paper["summary_retry_count"] = retry_count
            self.current_paper["summary_token_estimate"] = char_count // 4

    def log_hallucination_check(self, *, confidence: float, verified_count: int,
                                unverified_count: int, unverified_sentences: list[str],
                                repair_attempt: int = 0):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["hallucination_confidence"] = confidence
            self.current_paper["hallucination_verified_count"] = verified_count
            self.current_paper["hallucination_unverified_count"] = unverified_count
            self.current_paper["hallucination_repair_attempts"] = repair_attempt
            self.current_paper["hallucination_unverified_sentences"] = unverified_sentences

    def log_warning(self, warning_message: str):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["warnings"].append(warning_message)

    def log_error(self, error_message: str):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["errors"].append(error_message)

    def finish_paper(self):
        with self._lock:
            self._ensure_paper_started()
            self.current_paper["processing_time_seconds"] = round(time.time() - self.paper_start, 2)
            
            # Accumulate run stats safely
            self.total_papers += 1
            self.total_figures += self.current_paper["figures_processed"]
            self.total_errors += len(self.current_paper["errors"])
            self.total_tokens += self.current_paper.get("summary_token_estimate") or 0

            # Append to JSONL safely
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(self.current_paper) + '\n')
            
            # Reset current paper state
            self.current_paper = {}
            self.paper_start = 0.0

    def print_run_summary(self):
        with self._lock:
            total_time = round(time.time() - self.run_start, 2)
            papers = self.total_papers
            figures = self.total_figures
            errors = self.total_errors
            tokens = self.total_tokens
            log_path = self.log_path
            
        print("\n" + "="*50)
        print(" PIPELINE RUN SUMMARY")
        print("="*50)
        print(f" Total Papers Processed: {papers}")
        print(f" Total Figures Analyzed: {figures}")
        print(f" Total Errors:           {errors}")
        print(f" Total Estimated Tokens: {tokens}")
        print(f" Total Run Time:         {total_time} seconds")
        print(f" Log File Saved To:      {log_path}")
        print("="*50 + "\n")
