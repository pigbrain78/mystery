import zlib, os, re

# 1) are the two "dmg" files genuine UDIF disk images?
for p in ("/project/Ollama.dmg", "/project/Additional_Tools_for_Xcode_27_beta_4.dmg"):
    if not os.path.exists(p):
        print("MISSING (not shared into repo):", p)
        continue
    n = os.path.getsize(p)
    with open(p, "rb") as f:
        head = f.read(64)
        f.seek(max(0, n - 512))
        tail = f.read()
    print("=" * 60)
    print(p, n, "bytes")
    print("  head:", head[:8].hex())
    print("  trailer magic:", tail[0:4], "-> koly present:", b"koly" in tail)
    try:
        d = zlib.decompressobj()
        out = d.decompress(head * 200, 4096)
        print("  zlib stream ok, first bytes:", out[:40])
    except Exception as e:
        print("  zlib error:", e)

# 2) any personal paths / usernames leaked inside the skill + zip contents?
PAT = re.compile(r"/Users/[A-Za-z0-9_.\-]+|/home/[A-Za-z0-9_.\-]+|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[a-z]{2,}")
print("=" * 60)
found = {}
for d, _, fs in os.walk("extracted"):
    for f in fs:
        fp = os.path.join(d, f)
        try:
            txt = open(fp, errors="ignore").read()
        except Exception:
            continue
        for m in PAT.finditer(txt):
            found.setdefault(m.group(0), set()).add(fp)
for k, v in sorted(found.items()):
    print(f"  {k:<45} {len(v)} file(s)")
