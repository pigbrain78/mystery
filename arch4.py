import zipfile, re

p = "extracted/Archive/Give me the master code drop in..docx"
xml = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "ignore")
txt = re.sub(r"<[^>]+>", "", xml)
for m in re.finditer(r"0850104858", txt):
    print("context:", txt[max(0, m.start()-160):m.end()+160].replace("\n", " | "))
