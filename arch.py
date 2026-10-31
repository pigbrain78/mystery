import zipfile, os, hashlib, re, datetime

SRC = "zips/Archive.zip"
OUT = "extracted/Archive"
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(SRC)
infos = z.infolist()
print(f"{len(infos)} entries\n")

# match against the two iOS archives already here
def table(path, strip):
    zz = zipfile.ZipFile(path)
    return {i.filename[len(strip):]: hashlib.sha256(zz.read(i)).hexdigest()
            for i in zz.infolist() if not i.is_dir()}

mi = table("zips/Manus omi.zip", "ManusOmniAINetwork/")

n_saved = 0
for i in infos:
    n = i.filename
    print(f"{i.file_size:>9}  {datetime.datetime(*i.date_time):%Y-%m-%d %H:%M}  {n}")
    if i.is_dir():
        continue
    data = z.read(i)
    h = hashlib.sha256(data).hexdigest()
    known = ""
    for k, v in mi.items():
        if v == h:
            known = f"  == Manus omi.zip:{k}"
            break
    dest = os.path.join(OUT, n)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    n_saved += 1
    if known:
        print(f"      -> identical to {known}")
print(f"\nsaved {n_saved} files under {OUT}")
