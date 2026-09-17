"""Output validation and self-correction for structured summaries.

The 12-section contract is sourced from `prompts.py` so this module and
`genai_client.validate_structured_summary` can never disagree (Task 1 of
the ingestion-prompt overhaul plan).

Public surface preserved for backwards compatibility:

* `REQUIRED_HEADERS` — list[str] of the 12 ordered section headings.
* `ValidationResult` — dataclass returned by `SummaryValidator.validate`.
* `SummaryValidator` — `.validate(text)`, `.repair(text, missing)`,
  `.extract_entities(text)`.
* `EntityNormalizer` — alias-aware entity name canonicaliser.
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from prompts import required_headers as _required_headers
from molecular_roles import (
    enforced_role,
    find_role_contradictions,
    validate_role_record,
)


# REQUIRED_HEADERS is now sourced from prompts.REQUIRED_SECTIONS so there is
# exactly one place the 12-heading contract lives. Kept as a module-level
# list[str] for backwards compatibility — historical callers iterate over it
# directly.
REQUIRED_HEADERS: List[str] = _required_headers()


@dataclass
class ValidationResult:
    valid: bool
    missing_sections: List[str]
    errors: List[str]
    warnings: List[str]
    score: float  # 0-100


class SummaryValidator:
    """Validates structured summaries and suggests corrections."""
    
    def __init__(self):
        self.min_section_length = 20  # chars
    
    def validate(self, summary: str) -> ValidationResult:
        missing = []
        errors = []
        warnings = []
        found_headers = []
        
        # Determine paper type from frontmatter or heading structure
        paper_type = "primary_research"
        fm_match = re.search(r"^---\n(.*?)\n---", summary, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            pt_match = re.search(r"^paper_type:\s*(\w+)", fm_text, re.MULTILINE)
            if pt_match:
                paper_type = pt_match.group(1)
            elif "Reviewed Literature & Inclusion Criteria" in summary:
                paper_type = "review"
            elif "Correction Summary" in summary and "Original Citation" in summary:
                paper_type = "correction_notice"
        elif "Reviewed Literature & Inclusion Criteria" in summary:
            paper_type = "review"
        elif "Correction Summary" in summary and "Original Citation" in summary:
            paper_type = "correction_notice"

        import prompts
        required_headers_list = prompts.headers_for(paper_type)

        # Check each required header
        for header in required_headers_list:
            pattern = rf"(?i)^##\s*{re.escape(header)}\s*$"
            if re.search(pattern, summary, re.MULTILINE):
                found_headers.append(header)
                # Check if section has content
                match = re.search(pattern + r"\n+(.+?)(?=\n##|\Z)", summary, re.DOTALL | re.MULTILINE)
                if match:
                    content = match.group(1).strip()
                    if len(content) < self.min_section_length:
                        warnings.append(f"Section '{header}' has minimal content")
                else:
                    warnings.append(f"Section '{header}' may be empty")
            else:
                missing.append(header)
        
        # Check YAML frontmatter
        if not re.search(r'^---\n', summary, re.MULTILINE):
            errors.append("Missing YAML frontmatter")
        
        # Check wikilinks
        wikilinks = re.findall(r'\[\[(.*?)\]\]', summary)
        if len(wikilinks) < 3:
            warnings.append(f"Very few wikilinks ({len(wikilinks)}) - entities may not be linked")

        # Flag high-confidence ontology contradictions without invalidating
        # historical summaries that predate structured molecular-role fields.
        warnings.extend(find_role_contradictions(summary))

        # Calculate score
        score = 100
        score -= len(missing) * 10
        score -= len(errors) * 15
        score -= len(warnings) * 3
        score = max(0, score)
        
        valid = len(missing) == 0 and len(errors) == 0
        
        return ValidationResult(
            valid=valid,
            missing_sections=missing,
            errors=errors,
            warnings=warnings,
            score=score
        )
    
    def repair(self, summary: str, missing_sections: List[str]) -> str:
        """Add missing sections to summary."""
        repair_sections = {
            "Title & Metadata": "## Title & Metadata\nNot available in source text.\n",
            "Abstract Summary": "## Abstract Summary\nNot reported in this paper.\n",
            "Introduction & Background": "## Introduction & Background\nNot reported in this paper.\n",
            "Key Concepts & Theory": "## Key Concepts & Theory\nNot reported in this paper.\n",
            "Important Entities": "## Important Entities\nNot reported in this paper.\n",
            "Methods & Experimental Design": "## Methods & Experimental Design\nNot reported in this paper.\n",
            "Key Results & Data": "## Key Results & Data\nNot reported in this paper.\n",
            "Mechanistic Insights": "## Mechanistic Insights\nNot reported in this paper.\n",
            "Conclusions & Implications": "## Conclusions & Implications\nNot reported in this paper.\n",
            "Limitations & Caveats": "## Limitations & Caveats\nNot reported in this paper.\n",
            "Future Directions": "## Future Directions\nNot reported in this paper.\n",
            "Key References to Follow Up": "## Key References to Follow Up\nNot reported in this paper.\n"
        }
        
        # Add missing sections before the final source note or at end
        final_source_match = re.search(r'\n---\n\*\*Source PDF:.*$', summary)
        
        for section in missing_sections:
            if section in repair_sections:
                repair_text = repair_sections[section]
                if final_source_match:
                    summary = summary[:final_source_match.start()] + "\n" + repair_text + summary[final_source_match.start():]
                else:
                    summary += "\n" + repair_text
        
        return summary
    
    def extract_entities(self, summary: str) -> Dict[str, List[str]]:
        """Extract structured entities from summary."""
        entities = {
            "genes": [],
            "proteins": [],
            "species": [],
            "pathways": [],
            "methods": []
        }
        
        # Extract from Important Entities section
        entity_section = re.search(r'## Important Entities\n+(.+?)(?=\n##|\Z)', summary, re.DOTALL | re.IGNORECASE)
        if entity_section:
            content = entity_section.group(1)
            # Find all wikilinks
            links = re.findall(r'\[\[(.*?)\]\]', content)
            for link in links:
                link_lower = link.lower()
                if any(kw in link_lower for kw in ['gene', 'factor', 'kinase', 'synthase']):
                    entities["genes"].append(link)
                elif any(kw in link_lower for kw in ['protein', 'enzyme']):
                    entities["proteins"].append(link)
                elif any(kw in link_lower for kw in ['arabidopsis', 'maize', 'wheat', 'rice', 'sorghum', 'zea']):
                    entities["species"].append(link)
                elif any(kw in link_lower for kw in ['pathway', 'biosynthesis', 'metabolic']):
                    entities["pathways"].append(link)
                elif any(kw in link_lower for kw in ['crispr', 'transgenic', 'overexpression']):
                    entities["methods"].append(link)
        
        return entities


class EntityNormalizer:
    """Normalize entity names across papers."""
    
    # Common aliases for plant genes
    ALIASES = {
        "ZmMYB31": ["ZmMYB-31", "Zea mays MYB31", "MYB31"],
        "TaNAC019": ["TaNAC-019", "Triticum aestivum NAC019"],
        "ZmNAC34": ["ZmNAC-34", "Zea mays NAC34"],
        "AGPase": ["ADP-glucose pyrophosphorylase", "AGP"],
        "SS": ["starch synthase", "Starch Synthase"],
        "SBE": ["starch branching enzyme", "Branching Enzyme"],
    }
    
    @classmethod
    def normalize(cls, name: str) -> str:
        """Normalize entity name to canonical form."""
        for canonical, aliases in cls.ALIASES.items():
            if name in aliases or name.lower() == canonical.lower():
                return canonical
            for alias in aliases:
                if name.lower() == alias.lower():
                    return canonical
        return name
    
    @classmethod
    def get_aliases(cls, name: str) -> List[str]:
        """Get all aliases for a name."""
        for canonical, aliases in cls.ALIASES.items():
            if name.lower() == canonical.lower() or name in aliases:
                return [canonical] + aliases
        return [name]

    @classmethod
    def molecular_role(cls, name: str, proposed_role: str | None = None) -> str:
        """Return an ontology-safe role, applying high-confidence overrides."""
        return enforced_role(cls.normalize(name), proposed_role)

    @classmethod
    def validate_molecular_role(cls, record: Dict, source_text: str | None = None):
        """Validate role, directness, and exact role-evidence quotation."""
        return validate_role_record(record, source_text=source_text)