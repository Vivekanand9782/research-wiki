#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import re

def main():
    parser = argparse.ArgumentParser(description="Log a user-visible change in CHANGELOG.md")
    parser.add_argument("message", type=str, help="The changelog message")
    parser.add_argument("--section", type=str, required=True, choices=["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"], help="The section under [Unreleased] to append to")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    changelog_path = project_root / "CHANGELOG.md"

    if not changelog_path.exists():
        print(f"Error: {changelog_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the [Unreleased] header
    unreleased_pattern = re.compile(r'(## \[Unreleased\]\n)')
    match = unreleased_pattern.search(content)
    
    if not match:
        print("Error: '## [Unreleased]' section not found in CHANGELOG.md.", file=sys.stderr)
        sys.exit(1)

    insert_pos = match.end()
    
    # Check if the specific subsection exists under [Unreleased] before the next version
    # E.g., ### Added
    # Next version starts with ## [X.Y.Z]
    next_version_match = re.search(r'\n## \[[0-9]+', content[insert_pos:])
    end_of_unreleased = insert_pos + next_version_match.start() if next_version_match else len(content)

    unreleased_block = content[insert_pos:end_of_unreleased]
    
    section_header = f"### {args.section}"
    section_match = re.search(f'^{section_header}$', unreleased_block, re.MULTILINE)

    if section_match:
        # Append to existing section
        section_end = section_match.end()
        # Find next blank line or next header
        next_stuff = re.search(r'\n(###|##|\n\n)', unreleased_block[section_end:])
        if next_stuff:
            append_pos = insert_pos + section_end + next_stuff.start()
        else:
            append_pos = end_of_unreleased

        new_content = content[:append_pos] + f"\n- {args.message}" + content[append_pos:]
    else:
        # Create new section under [Unreleased]
        new_content = content[:insert_pos] + f"\n{section_header}\n- {args.message}\n" + content[insert_pos:]

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Logged change to {args.section} in CHANGELOG.md")

if __name__ == "__main__":
    main()
