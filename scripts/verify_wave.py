"""Post-wave verification for wiki source pages.
Usage: python3 verify_wave.py <wiki_path> ..."""
import sys, os
sys.path.insert(0, "/Users/vivekanandsirohi/Desktop/antigravity/research-wiki")
import validation, lint_wiki

paths = sys.argv[1:]
if not paths:
    print("Usage: verify_wave.py <wiki_path> ...")
    sys.exit(1)

all_ok = True
for fp in paths:
    if not os.path.exists(fp):
        print(f"MISSING: {fp}")
        all_ok = False
        continue
    t = open(fp, "r", errors="ignore").read()
    # Head-3 format_version check
    head3 = "\n".join(t.splitlines()[:3])
    fmt_ok = head3.count("format_version: 2") == 1

    v = validation.SummaryValidator().validate(t)
    l = lint_wiki.validate_source_page(t)

    wc = len(t.split())
    # Footnotes count
    import re
    fn = len(re.findall(r'\[\^[^\]]+\]', t))
    # Wikilinks
    wl = len(re.findall(r'\[\[[^\]]+\]\]', t))

    ok = fmt_ok and v.valid and v.score >= 90 and len(v.errors) == 0 and len(l) == 0
    status = "OK" if ok else "FAIL"
    print(f"{status} | {os.path.basename(fp)} | fmt_v2:{'Y' if fmt_ok else 'N'} | V:{v.valid} S:{v.score} LE:{len(v.errors)} LINT:{len(l)} | WC:{wc} FN:{fn} WL:{wl}")
    if not ok:
        all_ok = False
        if v.missing_sections:
            print("   missing:", v.missing_sections)
        if v.errors:
            print("   errors:", v.errors[:3])
        if l:
            print("   lint:", l[:3])

sys.exit(0 if all_ok else 1)