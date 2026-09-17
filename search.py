"""Backward-compatible facade for ResearchWiki retrieval.

The implementation lives in :mod:`research_retrieval`; this module preserves the
historical ``FullTextSearch``/``SearchResult`` imports and command-line entrypoint.
"""

from __future__ import annotations

import argparse

from research_retrieval import (
    DOC_TYPES,
    INDEX_VERSION,
    SEARCH_MODES,
    FullTextSearch,
    SearchResult,
)


class SearchCLI:
    """Command-line interface for quality-aware ResearchWiki search."""

    def __init__(self, wiki_folder: str = "wiki"):
        self.search = FullTextSearch(wiki_folder=wiki_folder)

    def run(
        self,
        query: str,
        verbose: bool = False,
        *,
        top_k: int = 10,
        mode: str = "hybrid",
        doc_type: str | None = None,
        include_stubs: bool = False,
        exhaustive: bool = False,
    ):
        results = self.search.search(
            query,
            top_k=top_k,
            mode=mode,
            doc_type=doc_type,
            include_stubs=include_stubs,
            exhaustive=exhaustive,
        )
        if not results:
            print("No results found.")
            print(self.search.last_search_report)
            return

        print(f"\nResults for {query!r}:\n")
        for index, result in enumerate(results, start=1):
            print(f"{index}. {result.title}")
            print(
                f"   [{result.paper}] score={result.score:.3f} "
                f"quality={result.evidence_quality:.2f} type={result.doc_type}"
            )
            if result.source_path:
                line_range = (
                    f":{result.line_start}-{result.line_end}"
                    if result.line_start is not None
                    else ""
                )
                print(f"   Evidence: {result.source_path}{line_range} ({result.section})")
            print(f"   {result.snippet}")
            if verbose:
                print(f"   Matches: {', '.join(result.matches)}")
                print(f"   Quality flags: {', '.join(result.quality_flags)}")
            print()

        if verbose:
            print("Coverage:")
            for key, value in self.search.last_search_report.items():
                print(f"  {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the ResearchWiki evidence corpus")
    parser.add_argument("query", nargs="+", help="Research query")
    parser.add_argument("--wiki", default="wiki", help="Wiki root (default: wiki)")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--mode", choices=SEARCH_MODES, default="hybrid")
    parser.add_argument("--doc-type", choices=DOC_TYPES)
    parser.add_argument("--include-stubs", action="store_true")
    parser.add_argument("--exhaustive", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    cli = SearchCLI(args.wiki)
    if args.rebuild:
        cli.search.build_index()
    cli.run(
        " ".join(args.query),
        verbose=args.verbose,
        top_k=args.top_k,
        mode=args.mode,
        doc_type=args.doc_type,
        include_stubs=args.include_stubs,
        exhaustive=args.exhaustive,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "DOC_TYPES",
    "INDEX_VERSION",
    "SEARCH_MODES",
    "FullTextSearch",
    "SearchCLI",
    "SearchResult",
]
