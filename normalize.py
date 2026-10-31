import zipfile, os, hashlib, re, glob

OUT = "skills-unpacked"
manifest = []

for path in sorted(glob.glob("skills/*.skill")):
    src = os.path.basename(path)
    name = src[:-len(".skill")]
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    z = zipfile.ZipFile(path)
    files = {}
    for i in z.infolist():
        if i.is_dir():
            continue
        n = i.filename
        if "__pycache__" in n or n.endswith(".pyc"):
            continue
        # flatten a duplicated top folder that just repeats the skill name
        parts = n.split("/")
        if parts and parts[0] == name:
            n = "/".join(parts[1:])
        if not n:
            continue
        data = z.read(i)
        # rewrite absolute sandbox paths to repo-relative ones
        if n.endswith((".md", ".txt", ".py", ".yml", ".yaml", ".json")):
            try:
                txt = data.decode("utf-8")
            except UnicodeDecodeError:
                txt = None
            if txt is not None:
                txt2 = re.sub(r"/(?:home|Users)/[A-Za-z0-9_.\-]+/skills/" + re.escape(name) + r"/", "", txt)
                if txt2 != txt:
                    print(f"  path-normalized: {name}/{n}")
                data = txt2.encode("utf-8")
        files[n] = data
    base = os.path.join(OUT, name)
    for n, data in files.items():
        dest = os.path.join(base, n)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
    manifest.append((name, src, digest, sorted(files)))
    print(f"{name}: {len(files)} files")

with open(os.path.join(OUT, "MANIFEST.md"), "w") as f:
    f.write("# Normalized skills\n\n")
    f.write("One folder per skill, ready to import elsewhere. Changes made:\n")
    f.write("absolute sandbox paths in docs rewritten to repo-relative,\n")
    f.write("`__pycache__` / `.pyc` dropped, `code-refactor-analyzer`'s duplicate\n")
    f.write("wrapper folder flattened. Sources stay in `skills/*.skill`.\n\n")
    for name, src, digest, files in manifest:
        f.write(f"## {name}\n\n- source: `skills/{src}`\n- sha256: `{digest}`\n")
        f.write(f"- files ({len(files)}):\n")
        for n in files:
            f.write(f"  - `{n}`\n")
        f.write("\n")
print("MANIFEST.md written")
