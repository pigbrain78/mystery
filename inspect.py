import zipfile, os, sys, json

roots = ["skills", "zips"]
for root in roots:
    for fn in sorted(os.listdir(root)):
        p = os.path.join(root, fn)
        print("=" * 70)
        print(p, os.path.getsize(p), "bytes")
        try:
            z = zipfile.ZipFile(p)
        except Exception as e:
            print("  NOT A ZIP:", e)
            continue
        names = z.namelist()
        print(f"  {len(names)} entries")
        for n in names:
            i = z.getinfo(n)
            print(f"   {i.file_size:>9}  {n}")
        print()
