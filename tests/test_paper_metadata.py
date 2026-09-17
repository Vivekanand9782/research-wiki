"""Offline regression tests for optional paper metadata enrichment."""
from __future__ import annotations

import json
from unittest.mock import patch

import paper_metadata as metadata


class FakeHTTPResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def test_doi_extraction_removes_html_and_markdown_suffixes():
    assert metadata.extract_doi_from_text(
        "DOI: 10.1080/07388551.2019.1709795</u>"
    ) == "10.1080/07388551.2019.1709795"
    assert metadata.extract_doi_from_text(
        "[doi](https://doi.org/10.1111/pbi.13433)."
    ) == "10.1111/pbi.13433"


def test_openalex_retries_empty_response_then_parses_json_without_unverified_tls():
    payload = {
        "title": "Example",
        "publication_year": 2020,
        "doi": "https://doi.org/10.1111/pbi.13433",
        "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
        "primary_location": {"source": {"display_name": "Plant Journal"}},
    }
    responses = [FakeHTTPResponse(b""), FakeHTTPResponse(json.dumps(payload).encode())]
    with (
        patch.object(metadata.urllib.request, "urlopen", side_effect=responses) as urlopen,
        patch.object(metadata.time, "sleep") as sleep,
    ):
        result = metadata._fetch_openalex(
            "https://doi.org/10.1111/pbi.13433</u>", max_retries=2
        )

    assert result == {
        "authors": ["Lovelace, A."],
        "year": 2020,
        "title": "Example",
        "journal": "Plant Journal",
        "doi": "10.1111/pbi.13433",
        "source": "openalex",
    }
    assert urlopen.call_count == 2
    assert sleep.call_count == 1
    for call in urlopen.call_args_list:
        assert "context" not in call.kwargs
        assert "</u>" not in call.args[0].full_url


def test_openalex_non_json_exhaustion_is_optional_and_returns_none():
    responses = [FakeHTTPResponse(b"not-json"), FakeHTTPResponse(b"still-not-json")]
    with (
        patch.object(metadata.urllib.request, "urlopen", side_effect=responses),
        patch.object(metadata.time, "sleep"),
    ):
        assert metadata._fetch_openalex("10.1038/nbt.3811", max_retries=2) is None
