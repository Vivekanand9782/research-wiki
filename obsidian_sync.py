"""Obsidian vault sync - export wiki to Obsidian-compatible format."""
import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ObsidianSync:
    """Sync research wiki to Obsidian vault."""
    
    def __init__(self, wiki_folder: str = "wiki", obsidian_vault: str = None):
        self.wiki_folder = Path(wiki_folder)
        self.obsidian_vault = Path(obsidian_vault) if obsidian_vault else self.wiki_folder / "obsidian_export"
        self.sources_folder = self.wiki_folder / "sources"
        
    def sync(self, clean: bool = False):
        """Sync all content to Obsidian vault."""
        print(f"🚀 Syncing to Obsidian vault: {self.obsidian_vault}")
        
        # Create vault structure
        self._create_vault_structure()
        
        # Clean if requested
        if clean:
            self._clean_vault()
        
        # Sync sources (papers)
        self._sync_sources()
        
        # Sync entities
        self._sync_entities()
        
        # Sync concepts
        self._sync_concepts()
        
        # Create index
        self._create_vault_index()
        
        print(f"✅ Sync complete: {self.obsidian_vault}")
    
    def _create_vault_structure(self):
        """Create Obsidian vault folders."""
        folders = [
            self.obsidian_vault,
            self.obsidian_vault / "sources",
            self.obsidian_vault / "entities",
            self.obsidian_vault / "concepts",
            self.obsidian_vault / "attachments",
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def _clean_vault(self):
        """Clean vault before fresh sync."""
        for item in self.obsidian_vault.iterdir():
            if item.name not in ['attachments', '.obsidian']:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    
    def _sync_sources(self):
        """Sync paper sources to vault."""
        sources_dest = self.obsidian_vault / "sources"
        
        if not self.sources_folder.exists():
            return
        
        for md_file in self.sources_folder.rglob("*.md"):
            # Copy with proper formatting
            content = md_file.read_text(encoding='utf-8')
            content = self._format_for_obsidian(content)
            
            dest = sources_dest / md_file.name
            dest.write_text(content, encoding='utf-8')
            
        print(f"  ✓ Synced {len(list(sources_dest.glob('*.md')))} papers")
    
    def _sync_entities(self):
        """Sync entity pages."""
        entities_src = self.wiki_folder / "entities"
        entities_dest = self.obsidian_vault / "entities"
        
        if not entities_src.exists():
            return
        
        for md_file in entities_src.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            content = self._format_for_obsidian(content)
            
            dest = entities_dest / md_file.name
            dest.write_text(content, encoding='utf-8')
            
        print(f"  ✓ Synced {len(list(entities_dest.glob('*.md')))} entities")
    
    def _sync_concepts(self):
        """Sync concept pages."""
        concepts_src = self.wiki_folder / "concepts"
        concepts_dest = self.obsidian_vault / "concepts"
        
        if not concepts_src.exists():
            return
        
        for md_file in concepts_src.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            content = self._format_for_obsidian(content)
            
            dest = concepts_dest / md_file.name
            dest.write_text(content, encoding='utf-8')
            
        print(f"  ✓ Synced {len(list(concepts_dest.glob('*.md')))} concepts")
    
    def _format_for_obsidian(self, content: str) -> str:
        """Format content for Obsidian compatibility."""
        # Ensure YAML frontmatter is proper
        if not content.startswith('---'):
            # Add frontmatter
            content = f"---\ndate_created: {datetime.now().date()}\n---\n\n{content}"
        
        # Update relative paths for images
        content = content.replace('../../raw/assets', '../attachments')
        
        # Ensure consistent wikilinks
        content = content.replace('[[', '[[')
        content = content.replace(']]', ']]')
        
        return content
    
    def _create_vault_index(self):
        """Create vault index/home page."""
        index_content = """# Research Wiki

## Index

### Papers
[[sources/index|View all papers]]

### Entities
[[entities/index|View all entities]]

### Concepts
[[concepts/index|View all concepts]]

---

*Last synced: {date}*
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        index_path = self.obsidian_vault / "index.md"
        index_path.write_text(index_content)
    
    def create_dataview_index(self):
        """Create Dataview.js index files for Obsidian."""
        # Sources index
        sources_index = """# Papers

```dataview
TABLE WITHOUT ID
  file.link as Paper,
  date_created as Created,
  type
FROM "sources"
SORT file.name ASC
```
"""
        (self.obsidian_vault / "sources" / "index.md").write_text(sources_index)
        
        # Entities index
        entities_index = """# Entities

```dataview
TABLE WITHOUT ID
  file.link as Entity,
  type,
  source_count as Sources
FROM "entities"
SORT file.name ASC
```
"""
        (self.obsidian_vault / "entities" / "index.md").write_text(entities_index)


if __name__ == "__main__":
    sync = ObsidianSync()
    sync.sync(clean=False)