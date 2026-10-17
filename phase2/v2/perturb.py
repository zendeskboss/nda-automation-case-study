"""Change test inputs: copies of C01, C05 and C12 with changes that must not change any decision.

1. The counterparty gets a different name (full name and short name, everywhere).
2. Extra spaces inside sentences and at line ends.
3. A blank line between every paragraph.
Clause numbers and wording stay the same. The originals in contracts/ are not touched.
"""
import os, re

V2 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(V2))
OUT = os.path.join(V2, "perturbed"); os.makedirs(OUT, exist_ok=True)

for cid in ["C01", "C05", "C12"]:
    t = open(os.path.join(ROOT, "contracts", cid + ".md"), encoding="utf-8").read()
    party = [l for l in t.splitlines() if re.match(r"^\s*\((1|2)\)", l) and "HALYARD" not in l][0]
    party = re.sub(r"\[\[DEL:.*?\]\]", "", party)
    full = re.search(r"((?:[A-Z0-9&.'-]+ ){1,6}[A-Z0-9&.'-]+),", party).group(1).strip()
    short = re.findall(r"""\(\s*(?:hereinafter (?:referred to as|called) )?["“]?([A-Z][A-Za-z]+)["”]?\s*\)""", party)
    reps = [(full, "ZEPHYR NORTHGATE HOLDINGS LIMITED")] + [(s, "Zephyr") for s in short if s not in ("Counterparty", "Halyard")]
    for a, b in reps: t = t.replace(a, b)
    lines = [re.sub(r"\. ", ".  ", l) + "  " for l in t.splitlines()]
    open(os.path.join(OUT, cid + ".md"), "w", encoding="utf-8").write("\n\n".join(lines) + "\n")
    print(cid, reps)
