"""Checks that every evidence snippet in golden_set.json exists in its source document.
Uses the same normalization you should use when labeling retrieved chunks as relevant."""
import json, re, sys
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]
def norm(t):
    t=t.replace("**","").replace("|"," ").replace("\u2013","-").replace("\u2014","-")
    return re.sub(r"\s+"," ",t).strip().lower()
def load(p):
    p=ROOT/"corpus"/p
    if p.suffix==".pdf": return " ".join(pg.extract_text() for pg in PdfReader(p).pages)
    return p.read_text()
gs=json.load(open(ROOT/"eval/golden_set.json")); cache={}; bad=0
for q in gs["questions"]:
    for e in q["evidence"]:
        src=e["source"]
        if src not in cache: cache[src]=norm(load(src))
        if norm(e["text"]) not in cache[src]:
            bad+=1; print(f"MISSING {q['id']} [{src}] -> {e['text']}")
print(f"{len(gs['questions'])} questions checked, {bad} missing evidence snippets")
sys.exit(1 if bad else 0)
