import os, re

SUS = re.compile(
    r"requests\.(post|put|get|Session)|urllib|httpx|socket\.|subprocess|os\.system|"
    r"os\.popen|eval\(|exec\(|__import__|base64|shutil\.copy|expanduser|"
    r"open\(\s*['\"]/(Users|home|etc|var)|keychain|login\.keychain|"
    r"~/\.ssh|id_rsa|\.env\b|token|api_key|password|secret",
    re.I,
)

for d, _, fs in os.walk("extracted"):
    for f in sorted(fs):
        if not f.endswith((".py", ".swift", ".md", ".yml", ".m")):
            continue
        fp = os.path.join(d, f)
        lines = open(fp, errors="ignore").read().splitlines()
        hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if SUS.search(l)]
        if hits:
            print("#" * 60)
            print(fp)
            for n, l in hits[:14]:
                print(f"  {n}: {l[:150]}")
            if len(hits) > 14:
                print(f"  ... {len(hits) - 14} more")
