import zipfile, os, datetime, hashlib

SRC = "zips/Archive-3.zip"
OUT = "extracted/Archive-3"
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(SRC)
infos = z.infolist()
print(f"{len(infos)} entries\n")

# hash table of the smaller Archive.zip for comparison
def table(path, strip=0):
    zz = zipfile.ZipFile(path)
    d = {}
    for i in zz.infolist():
        if i.is_dir():
            continue
        k = i.filename[len(strip):] if strip else i.filename
        d[k] = hashlib.sha256(zz.read(i)).hexdigest()
    return d

prev = table("zips/Archive.zip")

dup = 0
saved = 0
for i in infos:
    n = i.filename
    print(f"{i.file_size:>10}  {datetime.datetime(*i.date_time):%Y-%m-%d %H:%M}  {n}")
    if i.is_dir():
        continue
    h = hashlib.sha256(z.read(i)).hexdigest()
    if n in prev and prev[n] == h:
        print("      == identical to Archive.zip:" + n)
        dup += 1
    dest = os.path.join(OUT, n)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(z.read(i))
    saved += 1
print(f"\n{dup} entries byte-identical with Archive.zip; saved {saved} to {OUT}")
