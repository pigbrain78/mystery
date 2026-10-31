import zipfile, os, re, io, hashlib, glob, json

# ---- 1. unpack the inner OKComputer zip ----
inner = "extracted/Archive/OKComputer_Self\u00a3\u00e6Modifying_Workflow_Engine.zip"
# the mojibake name may differ; find it
cand = [p for p in glob.glob("extracted/Archive/*.zip") if "OKComputer" in p]
print("inner zips:", cand)
for c in cand:
    z = zipfile.ZipFile(c)
    print(f"  {len(z.infolist())} entries")
    base = "extracted/OKComputer"
    for i in z.infolist():
        if i.is_dir():
            continue
        dest = os.path.join(base, i.filename)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(z.read(i))
        print(f"   {i.file_size:>8}  {i.filename}")

# ---- 2. text of every docx (word/document.xml) ----
def docx_text(p):
    try:
        z = zipfile.ZipFile(p)
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except Exception as e:
        return None
    xml = re.sub(r"<w:p[ >]", "\n<w:p ", xml)
    txt = re.sub(r"<[^>]+>", "", xml)
    return txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

CORPUS = {}
for p in glob.glob("extracted/Archive/*.docx"):
    t = docx_text(p)
    if t:
        CORPUS[os.path.basename(p)] = t
for p in glob.glob("extracted/OKComputer/**/*", recursive=True):
    if os.path.isfile(p):
        try:
            CORPUS["OKComputer/" + os.path.basename(p)] = open(p, errors="ignore").read()
        except Exception:
            pass
for p in ("extracted/Archive/distributed_agent_system.py",
          "extracted/Archive/happy-path.json",
          "extracted/Archive/seed.ts",
          "extracted/Archive/vite.config.ts"):
    if os.path.exists(p):
        CORPUS[os.path.basename(p)] = open(p, errors="ignore").read()

print(f"\ncorpus: {len(CORPUS)} docs, {sum(len(v) for v in CORPUS.values())} chars")

# ---- 3. secrets / personal info scan ----
PATS = {
    "api_key_sk":   r"sk-[A-Za-z0-9_\-]{12,}",
    "openai_old":   r"sk-proj-[A-Za-z0-9_\-]{12,}",
    "anthropic":    r"sk-ant-[A-Za-z0-9_\-]{12,}",
    "aws":          r"(?:AKIA|ASIA)[0-9A-Z]{16}",
    "github_tok":   r"gh[pousr]_[A-Za-z0-9]{20,}",
    "private_key":  r"BEGIN [A-Z ]*PRIVATE KEY",
    "jwt":          r"eyJ[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{10,}\.",
    "email":        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[a-z]{2,}",
    "phone":        r"\+?1?[-. ]?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
    "password_lit": r"(?:password|passwd|secret|token|api[_\-]?key)\s*[:=]\s*['\"][^'\"]{6,}",
    "db_url":       r"(?:postgres|mysql|mongodb)(?:\+\w+)?://[^\s'\"<>]{8,}",
    "ip_addr":      r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "sandbox_path": r"/(?:Users|home)/[A-Za-z0-9_.\-]+",
}
hits = {}
for name, txt in CORPUS.items():
    for label, pat in PATS.items():
        for m in re.finditer(pat, txt):
            val = m.group(0)
            if label == "ip_addr" and (val.startswith(("0.", "127.", "255.")) or val in ("1.1.1.1", "8.8.8.8")):
                continue
            hits.setdefault(label, {}).setdefault(val[:80], set()).add(name)
print("\n---- hits ----")
for label in sorted(hits):
    print(f"\n[{label}]")
    for val, files in sorted(hits[label].items(), key=lambda kv: -len(kv[1]))[:12]:
        fl = next(iter(files))
        print(f"  {val!r:<70} x{len(files):<3} e.g. {fl[:60]}")

json.dump({k: {v: sorted(f) for v, f in d.items()} for k, d in hits.items()},
          open("arch_hits.json", "w"), indent=1)

# ---- 4. hash the code files for cross-repo comparison ----
print("\n---- code hashes ----")
for p in ("extracted/Archive/distributed_agent_system.py",
          "extracted/Archive/package.json",
          "extracted/Archive/seed.ts",
          "extracted/Archive/vite.config.ts",
          "extracted/Archive/happy-path.json"):
    if os.path.exists(p):
        print(hashlib.sha256(open(p, "rb").read()).hexdigest()[:16], p)
