# Portfolio & Project Information

This repository represents a personal engineering portfolio and research platform by **Vivekanand Sirohi**.

---

## 📌 Project Overview

**Research Wiki & Local RAG** is an advanced scientific information analysis platform:
- **Sub-millisecond Local RAG**: SQLite FTS5 BM25 raw passage retrieval over academic literature with section-aware Maximal Marginal Relevance (MMR).
- **Multi-Hop Citation Agent**: Navigates paper citation networks (`papers_citing`, `related_papers`, `citation_chain`).
- **Autonomous Knowledge Graph**: Ingests scientific literature and generates Obsidian-compatible markdown vaults with bidirectional `[[wikilinks]]`.
- **Rigorous Verification**: All 441 regression unit tests run offline in ~30 seconds.

---

## 🧪 Local Testing & Evaluation

For recruiters, reviewers, or interviewers wishing to evaluate the test suite and software quality locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Vivekanand9782/research-wiki.git
   cd research-wiki
   ```

2. **Set up virtual environment & dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run automated regression tests**:
   ```bash
   pytest tests/ -v
   ```
   All 441 unit tests run locally using deterministic fixtures.

---

## ⚖️ Intellectual Property Notice

Copyright © 2026 Vivekanand Sirohi. All Rights Reserved.
Unauthorized copying, reproduction, redistribution, modification, or commercial use is strictly prohibited.
