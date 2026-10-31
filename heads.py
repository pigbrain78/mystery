import os, re, glob

for fp in sorted(glob.glob("extracted/**/SKILL.md", recursive=True)):
    txt = open(fp, errors="ignore").read()
    m = re.search(r"^---\n(.*?)\n---", txt, re.S)
    print("=" * 60)
    print(fp)
    if m:
        print(m.group(1).strip()[:700])
    print("  first heading:", (re.search(r"^# (.+)$", txt, re.M) or [None, "-"])[1])
