import zipfile, os, re, io

os.makedirs("extracted", exist_ok=True)

# 1. dump all text entries out of every zip
for root in ("skills", "zips"):
    for fn in sorted(os.listdir(root)):
        p = os.path.join(root, fn)
        if not zipfile.is_zipfile(p):
            continue
        z = zipfile.ZipFile(p)
        base = os.path.join("extracted", fn.replace(".skill", "").replace(".zip", ""))
        for i in z.infolist():
            if i.is_dir():
                continue
            if i.filename.endswith((".png", ".jpg", ".pyc")):
                continue
            dest = os.path.join(base, i.filename)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(z.read(i))

print("---- extracted ----")
for d, _, fs in os.walk("extracted"):
    for f in fs:
        fp = os.path.join(d, f)
        print(f"{os.path.getsize(fp):>8}  {fp}")

PAT = re.compile(
    r"sk-[A-Za-z0-9_\-]{8,}|AKIA[0-9A-Z]{12,}|BEGIN [A-Z ]*PRIVATE KEY|"
    r"https?://[^\s\"'`)<>]+|ec2-user|manus|Manus|cloudfront|copilot|agent|@[a-z0-9.\-]+\.(?:com|io|org|ai)",
)
print("\n---- hits ----")
seen = {}
for d, _, fs in os.walk("extracted"):
    for f in fs:
        fp = os.path.join(d, f)
        try:
            txt = open(fp, "r", errors="ignore").read()
        except Exception:
            continue
        for m in PAT.finditer(txt):
            k = m.group(0)
            seen.setdefault(k, set()).add(fp)
for k in sorted(seen):
    print(f"{k}   <- {sorted(seen[k])[:2]}")
