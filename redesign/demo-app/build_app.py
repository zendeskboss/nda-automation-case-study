"""Build app.html: the redesigned demo review app, with the 30 saved reviews built in.

Run: python3 redesign/demo-app/build_app.py   (writes redesign/demo-app/app.html)

It routes every saved review in replay/ with review.route, the same code that demo/build_demo.py uses,
and puts the contracts and the routed findings into app.src.html. No server and no API key are used.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# The engine folder: the nearest folder above this script that holds review.py
# (the project root here, engine/ in the hand-over package).
ROOT = os.path.dirname(HERE)
while not os.path.exists(os.path.join(ROOT, "review.py")):
    if os.path.dirname(ROOT) == ROOT:
        raise SystemExit("review.py not found above " + HERE)
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
import review  # noqa: E402


def build():
    pb = review.load_playbook()
    contracts, results, samples = {}, {}, []
    for p in sorted(glob.glob(os.path.join(ROOT, "contracts", "C??.md"))):
        cid = os.path.basename(p)[:3]
        rp = os.path.join(ROOT, "replay", cid + ".raw.json")
        if not os.path.exists(rp):
            continue
        raw = json.load(open(rp, encoding="utf-8"))
        contracts[cid] = open(p, encoding="utf-8").read()
        results[cid] = review.route(raw, pb, text=contracts[cid])
        samples.append(dict(id=cid, paper=raw.get("paper", "")))
    data = dict(status=dict(model="saved reviews", playbook=pb["meta"]["version"], threshold=review.DEFAULT_THRESHOLD),
                samples=samples, contracts=contracts, results=results)
    blob = json.dumps(data, ensure_ascii=False).replace("</", r"<\/")
    src = open(os.path.join(HERE, "app.src.html"), encoding="utf-8").read()
    if "__DATA__" not in src:
        raise SystemExit("app.src.html has no __DATA__ marker")
    out = os.path.join(HERE, "app.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(src.replace("__DATA__", blob, 1))
    print("wrote %s: %d contracts, %d KB" % (out, len(samples), os.path.getsize(out) // 1024))


if __name__ == "__main__":
    build()
