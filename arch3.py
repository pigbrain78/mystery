import hashlib, re, json, os

# 1. is the loose Archive/package.json identical to the inner OKComputer one?
a = open("extracted/Archive/package.json", "rb").read()
b = open("extracted/OKComputer/app/package.json", "rb").read()
print("loose package.json == OKComputer/app/package.json:", hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest())
c = open("extracted/Archive/vite.config.ts", "rb").read()
d = open("extracted/OKComputer/app/vite.config.ts", "rb").read()
print("loose vite.config.ts == OKComputer/app/vite.config.ts:", hashlib.sha256(c).hexdigest() == hashlib.sha256(d).hexdigest())

# 2. context around the phone-shaped number
txt = open("extracted/Archive/Give me the master code drop in..docx", errors="ignore").read()
for m in re.finditer(r"0850104858", txt):
    print("\ncontext:", txt[max(0, m.start()-120):m.end()+120].replace("\n", " | "))

# 3. .env.example contents (template only, confirm no real values)
print("\n---- .env.example ----")
print(open("extracted/OKComputer/app/.env.example").read())
