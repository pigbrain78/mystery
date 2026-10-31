import zipfile, os, hashlib, glob, re

z = zipfile.ZipFile("zips/Archive.zip")
print(f"{len(z.infolist())} entries")
base = "extracted/memorybrain"
for i in z.infolist():
    if i.is_dir():
        continue
    dest = os.path.join(base, i.filename)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(z.read(i))
print("extracted to", base)

def digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

# our side: memory_brain modules from this zip
mine = {}
for p in glob.glob(f"{base}/memory_brain/memory_brain/*.py"):
    mine[os.path.basename(p)] = digest(p)

# earlier skill package
skill = {}
for p in glob.glob("skills-unpacked/memory-second-brain/**/*.py", recursive=True):
    skill[os.path.basename(p)] = digest(p)

print(f"\nzip modules: {len(mine)}, skill modules: {len(skill)}")
same = diff = 0
for name, h in sorted(mine.items()):
    if name in skill:
        if skill[name] == h:
            same += 1
            print(f"  == {name}")
        else:
            diff += 1
            print(f"  != {name} (differs)")
    else:
        print(f"  +  {name} (not in skill)")
only_skill = [n for n in skill if n not in mine]
print(f"\nidentical: {same}, differ: {diff}, only in skill: {len(only_skill)}")

# quick secret scan of the whole zip
PATS = [r"sk-[A-Za-z0-9_\-]{12,}", r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"(?:AKIA|ASIA)[0-9A-Z]{16}", r"BEGIN [A-Z ]*PRIVATE KEY",
        r"(?:password|secret|token|api[_\-]?key)\s*[:=]\s*['\"][^'\"]{6,}",
        r"(?:postgres|mysql|mongodb)://[^\s'\"<>]{8,}"]
hits = 0
for p in glob.glob(f"{base}/**/*", recursive=True):
    if not os.path.isfile(p):
        continue
    try:
        t = open(p, errors="ignore").read()
    except Exception:
        continue
    for pat in PATS:
        for m in re.finditer(pat, t):
            print("HIT", pat[:20], m.group(0)[:50], "in", p)
            hits += 1
print(f"\nsecret hits: {hits}")
