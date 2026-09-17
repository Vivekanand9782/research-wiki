"""Shared molecular-role ontology and evidence validation for ResearchWiki."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


MOLECULAR_ROLES = (
    "sequence_specific_transcription_factor",
    "transcriptional_coregulator",
    "chromatin_regulator",
    "signaling_regulator",
    "enzyme",
    "receptor_or_kinase",
    "noncoding_rna",
    "locus_or_uncharacterized_protein",
)

EVIDENCE_DIRECTNESS = ("direct", "indirect", "review_summary", "unclear")

ROLE_DEFINITIONS = {
    "sequence_specific_transcription_factor": (
        "A protein explicitly established as binding DNA in a sequence-specific "
        "manner, usually through a named DNA-binding domain."
    ),
    "transcriptional_coregulator": (
        "A regulator of transcription that acts through protein interactions or "
        "recruitment without established independent sequence-specific DNA binding."
    ),
    "chromatin_regulator": (
        "A chromatin remodeler, histone modifier, DNA methylation factor, or "
        "chromatin-complex component."
    ),
    "signaling_regulator": (
        "A signaling/developmental regulator without established sequence-specific "
        "DNA binding. MFT/TaMFT/TaPHS1 PEBP-family proteins belong here."
    ),
    "enzyme": "A catalytic metabolic enzyme that is not a receptor or kinase.",
    "receptor_or_kinase": "A receptor, kinase, phosphatase, or kinase-cascade component.",
    "noncoding_rna": "A microRNA, siRNA, antisense RNA, or long non-coding RNA.",
    "locus_or_uncharacterized_protein": (
        "A locus, QTL, unresolved candidate, or protein whose molecular role is not established."
    ),
}

_ROLE_OVERRIDES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^(?:at|ta|os|hv|bd)?mft(?:1|2)?(?:[-_]?[a-z0-9]+)?$|^taphs1$", re.I),
        "signaling_regulator",
    ),
    (
        re.compile(r"^(?:della(?:proteins?)?|gai|rga|rgl[123]|slr1)$", re.I),
        "transcriptional_coregulator",
    ),
)


@dataclass(frozen=True)
class MolecularRoleValidation:
    valid: bool
    normalized_role: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def enforced_role(entity: str, proposed_role: Any = None) -> str:
    raw = str(entity or "").strip()
    compact = re.sub(r"[^a-z0-9]+", "", raw.lower())
    for pattern, role in _ROLE_OVERRIDES:
        if pattern.fullmatch(raw) or pattern.fullmatch(compact):
            return role
    proposed = str(proposed_role or "").strip()
    if proposed in MOLECULAR_ROLES:
        return proposed
    return "locus_or_uncharacterized_protein"


def ontology_prompt_block() -> str:
    definitions = "\n".join(
        f"- {role}: {ROLE_DEFINITIONS[role]}" for role in MOLECULAR_ROLES
    )
    return (
        "MOLECULAR ROLE ONTOLOGY (choose exactly one per gene/protein):\n"
        f"{definitions}\n"
        "Only sequence_specific_transcription_factor counts as a transcription "
        "factor in strict TF results. Never infer DNA binding from regulation of "
        "gene expression. DELLA proteins are transcriptional_coregulator; "
        "MFT/TaMFT/TaPHS1 are signaling_regulator, not TFs.\n"
        "For structured JSON, every entities[] gene/protein must include "
        "molecular_role, evidence_directness, role_evidence_quote (an exact "
        "contiguous source quote), and source_section. For Markdown Important "
        "Entities, append the molecular-role token and evidence directness to "
        "each gene/protein description. Use locus_or_uncharacterized_protein "
        "when the source does not establish a molecular role."
    )


def validate_role_record(
    record: Mapping[str, Any],
    *,
    source_text: str | None = None,
) -> MolecularRoleValidation:
    entity = str(record.get("text") or record.get("entity") or "").strip()
    proposed = str(record.get("molecular_role") or "").strip()
    normalized = enforced_role(entity, proposed)
    errors: list[str] = []
    warnings: list[str] = []

    if not entity:
        errors.append("entity/text is required")
    if proposed not in MOLECULAR_ROLES:
        errors.append(f"molecular_role must be one of {MOLECULAR_ROLES}")
    if proposed and normalized != proposed:
        errors.append(
            f"{entity or 'entity'} cannot be classified as {proposed}; enforced role is {normalized}"
        )

    quote = str(record.get("role_evidence_quote") or "").strip()
    directness = str(record.get("evidence_directness") or "").strip()
    if directness not in EVIDENCE_DIRECTNESS:
        errors.append(f"evidence_directness must be one of {EVIDENCE_DIRECTNESS}")
    if not quote:
        warnings.append("role_evidence_quote is missing")
    elif source_text is not None:
        normalized_quote = re.sub(r"\s+", " ", quote).strip()
        normalized_source = re.sub(r"\s+", " ", source_text)
        if normalized_quote not in normalized_source:
            errors.append("role_evidence_quote was not found in source text")

    if normalized == "sequence_specific_transcription_factor" and directness in {
        "indirect", "review_summary", "unclear", ""
    }:
        warnings.append(
            "strict TF classification lacks direct sequence-specific DNA-binding evidence"
        )
    return MolecularRoleValidation(
        valid=not errors,
        normalized_role=normalized,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def find_role_contradictions(summary: str) -> list[str]:
    """Find known high-confidence category errors in generated prose."""
    warnings: list[str] = []
    for line_number, line in enumerate(summary.splitlines(), start=1):
        normalized = re.sub(r"[*_\[\]|]", "", line).lower()
        if "transcription factor" not in normalized:
            continue
        if re.search(r"\b(?:ta)?mft(?:[-_ ]?[a-z0-9]+)?\b|\btaphs1\b", normalized):
            warnings.append(
                f"Line {line_number}: MFT/TaMFT/TaPHS1 is a PEBP-family signaling regulator, not a strict TF"
            )
        if re.search(r"\bdella(?: proteins?)?\b|\brgl[123]\b|\bgai\b|\brga\b", normalized):
            warnings.append(
                f"Line {line_number}: DELLA is a transcriptional coregulator, not a strict sequence-specific TF"
            )
    return warnings


__all__ = [
    "EVIDENCE_DIRECTNESS",
    "MOLECULAR_ROLES",
    "MolecularRoleValidation",
    "ROLE_DEFINITIONS",
    "enforced_role",
    "find_role_contradictions",
    "ontology_prompt_block",
    "validate_role_record",
]
