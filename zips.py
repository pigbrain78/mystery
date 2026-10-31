import zipfile, os, hashlib, datetime

a = "zips/Manus omi.zip"
b = "zips/ba60e2d0-50c4-4c51-b250-ee02bfae89ca-ios-src.zip"


def table(path, strip):
    z = zipfile.ZipFile(path)
    out = {}
    for i in z.infolist():
        if i.is_dir():
            continue
        n = i.filename
        if n.startswith(strip):
            n = n[len(strip):]
        out[n] = hashlib.sha256(z.read(i)).hexdigest()
    return out


ta = table(a, "ManusOmniAINetwork/")
tb = table(b, "")
print("A entries:", len(ta), "B entries:", len(tb))
same = [k for k in ta if k in tb and ta[k] == tb[k]]
diff = [k for k in ta if k in tb and ta[k] != tb[k]]
onlya = sorted(set(ta) - set(tb))
onlyb = sorted(set(tb) - set(ta))
print("identical:", len(same), " differing:", diff, " only in A:", onlya, " only in B:", onlyb)

print("\nzip modification timestamps (inner files, newest 8):")
rows = []
for path in ("skills", "zips"):
    for fn in sorted(os.listdir(path)):
        p = os.path.join(path, fn)
        if not zipfile.is_zipfile(p):
            continue
        z = zipfile.ZipFile(p)
        ds = [i.date_time for i in z.infolist() if not i.is_dir()]
        if ds:
            lo, hi = min(ds), max(ds)
            rows.append((hi, lo, fn))
for hi, lo, fn in sorted(rows, reverse=True):
    print(f"  {datetime.datetime(*lo):%Y-%m-%d %H:%M} -> {datetime.datetime(*hi):%Y-%m-%d %H:%M}   {fn}")
