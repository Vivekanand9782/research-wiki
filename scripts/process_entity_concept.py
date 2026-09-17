import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WIKI_SOURCES_DIR = BASE_DIR / "wiki" / "sources" / "uncategorized"
WIKI_ENTITIES_DIR = BASE_DIR / "wiki" / "entities"
WIKI_CONCEPTS_DIR = BASE_DIR / "wiki" / "concepts"

WIKI_ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
WIKI_CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)

TODAY = "2026-07-08"

def clean_slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()

def parse_definitions(text: str) -> dict:
    """Parse lines like '* **[[wikilink]]**: description' or '* [[wikilink]]: description'"""
    defs = {}
    for line in text.split("\n"):
        line = line.strip()
        # Match * **[[link]]**: desc or * [[link]]: desc with potential leading asterisks/indents
        m = re.search(r"^(?:[\*\-\s]+)?(?:\*\*)?\[\[(.*?)\]\](?:\*\*)?:?\s*(.*)$", line)
        if m:
            link_name = m.group(1).strip()
            desc = m.group(2).strip()
            # Clean up leading colons or dashes in desc
            desc = re.sub(r"^[:\-\s\u2013\u2014]+", "", desc).strip()
            if link_name and desc:
                defs[link_name] = desc
    return defs

def generate_page(name: str, desc: str, source_slug: str, page_type: str, existing_content: str = None) -> str:
    if existing_content:
        # Update existing page
        findings_header = f"### Findings from [[{source_slug}]]"
        if findings_header in existing_content:
            return existing_content
        
        # Count existing sources
        source_count = existing_content.count("[[") - existing_content.count(f"[[{source_slug}]]")
        if source_count <= 0:
            source_count = 1
        source_count += 1

        new_source = f"- [[{source_slug}]]"
        new_finding = f"\n{findings_header}\n{desc}"

        # Update metadata
        existing_content = re.sub(r"source_count:\s*\d+", f"source_count: {source_count}", existing_content)
        existing_content = re.sub(r"date_updated:\s*\S+", f"date_updated: {TODAY}", existing_content)
        existing_content = re.sub(r"Last updated:\s*\S+", f"Last updated: {TODAY}", existing_content)

        # Insert new source under Sources section
        if "**Sources**:" in existing_content:
            existing_content = re.sub(r"(\*\*Sources\*\*:\n)", rf"\1{new_source}\n", existing_content)
        elif "- [[ " in existing_content or "- [[" in existing_content:
            # Fallback insertion
            pass

        # Insert findings block before Related pages
        if "## Related pages" in existing_content:
            existing_content = existing_content.replace("## Related pages", f"{new_finding}\n\n## Related pages")
        else:
            existing_content += f"\n{new_finding}\n"
        
        return existing_content

    # Create new page
    return f"""---
tags: [{page_type}]
type: {page_type}
date_created: {TODAY}
date_updated: {TODAY}
source_count: 1
---

# {name}

**Summary**:
{desc}

**Sources**:
- [[{source_slug}]]

**Last updated**: {TODAY}

---

### Findings from [[{source_slug}]]
{desc}

## Related pages
"""

def process_source_file(source_path: Path):
    source_slug = source_path.stem
    content = source_path.read_text(encoding="utf-8")
    
    # Extract sections
    def get_section(heading):
        m = re.search(rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s+|\Z)", content, re.DOTALL | re.MULTILINE)
        return m.group(1).strip() if m else ""
        
    concepts_text = get_section("Key Concepts & Theory")
    entities_text = get_section("Important Entities")
    
    concepts = parse_definitions(concepts_text)
    entities = parse_definitions(entities_text)
    
    print(f"Processing source {source_slug}:")
    print(f"  Found {len(concepts)} concepts: {list(concepts.keys())}")
    print(f"  Found {len(entities)} entities: {list(entities.keys())}")
    
    # Process Concepts
    for name, desc in concepts.items():
        slug = clean_slug(name)
        if not slug or slug in ("genes-proteins", "organisms", "tools-techniques"):
            continue
        dest_path = WIKI_CONCEPTS_DIR / f"{slug}.md"
        existing = dest_path.read_text(encoding="utf-8") if dest_path.exists() else None
        new_content = generate_page(name, desc, source_slug, "concept", existing)
        dest_path.write_text(new_content, encoding="utf-8")
        
    # Process Entities
    for name, desc in entities.items():
        slug = clean_slug(name)
        if not slug or slug in ("genes-proteins", "organisms", "tools-techniques"):
            continue
        dest_path = WIKI_ENTITIES_DIR / f"{slug}.md"
        existing = dest_path.read_text(encoding="utf-8") if dest_path.exists() else None
        new_content = generate_page(name, desc, source_slug, "entity", existing)
        dest_path.write_text(new_content, encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_entity_concept.py <path_to_source_md>")
        sys.exit(1)
    process_source_file(Path(sys.argv[1]))
