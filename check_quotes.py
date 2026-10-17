"""Check that every quote in replay/ is an exact substring of its contract.

    python3 check_quotes.py            (run from engine/)

Prints each quote that fails and exits with status 1 if any fail.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    total, bad = 0, 0
    for path in sorted(glob.glob(os.path.join(HERE, "replay", "C??.raw.json"))):
        cid = os.path.basename(path)[:3]
        with open(os.path.join(HERE, "contracts", cid + ".md"), encoding="utf-8") as f:
            text = f.read()
        with open(path, encoding="utf-8") as f:
            findings = json.load(f)["findings"]
        for f in findings:
            total += 1
            if (f.get("quote") or "") not in text:
                bad += 1
                print("%s clause %s: quote not found: %r" % (cid, f.get("clause_no"), (f.get("quote") or "")[:80]))
    print("%d quotes checked, %d not found" % (total, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
