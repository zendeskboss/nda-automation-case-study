"""Build the hand-over package for a reader who has never seen this project.

Writes dist/NDA review case study/ and "NDA review case study.zip" next to this script.
The working folder is not changed. engine/ keeps the paths that review.py and server.py expect.

    python3 review.py --all --backend file --contracts contracts --out preds
    python3 evals/run_evals.py && python3 tools/make_story.py && python3 tools/make_review_page.py
    python3 redesign/demo-app/build_app.py && python3 build_package.py

The first line re-routes the saved reviews. The second runs the evals and writes the page data and all-reviews.html.
The second also writes the story pages (case-study.html and deeper/). The third rebuilds demo.html, then packs.
"""
import os, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "NDA review case study"
DIST = os.path.join(HERE, "dist")
OUT = os.path.join(DIST, NAME)
ZIP = os.path.join(HERE, NAME + ".zip")

# (source in this folder, path in the package)
FILES = [
    ("PACKAGE_README.md", "README.md"),
    # The reader-facing story: complete documents, built by tools/make_story.py.
    ("redesign/story/case-study.html", "case-study.html"),
    ("redesign/story/deeper/rules.html", "deeper/rules.html"),
    ("redesign/story/deeper/tool.html", "deeper/tool.html"),
    ("redesign/story/deeper/testing.html", "deeper/testing.html"),
    ("redesign/story/deeper/safety.html", "deeper/safety.html"),
    ("redesign/story/deeper/building.html", "deeper/building.html"),
    ("redesign/story/deeper/second-reader.html", "deeper/second-reader.html"),
    ("redesign/story/deeper/phase-2.html", "deeper/phase-2.html"),
    ("redesign/story/deeper/assumptions.html", "deeper/assumptions.html"),
    ("review.html", "all-reviews.html"),
    ("discovery/process_discovery_workbook.xlsx", "discovery/process-discovery-workbook.xlsx"),
    ("worksheet/playbook_worksheet.xlsx", "rules/playbook-worksheet.xlsx"),
    ("worksheet/worksheet_to_yaml.py", "rules/worksheet_to_yaml.py"),
    ("RUN_NOTES.md", "notes/run-notes.md"),
    ("tools/make_review_page.py", "engine/tools/make_review_page.py"),
    ("CLAUDE.md", "notes/ai-reviewer-instructions.md"),
    ("review.py", "engine/review.py"),
    ("check_quotes.py", "engine/check_quotes.py"),
    ("server.py", "engine/server.py"),
    ("playbook.yaml", "engine/playbook.yaml"),
    ("static/index.html", "engine/static/index.html"),
    ("redesign/demo-app/build_app.py", "engine/demo/build_app.py"),
    ("redesign/demo-app/app.src.html", "engine/demo/app.src.html"),
]

# The two pages, built from redesign/ (run redesign/build.mjs and redesign/demo-app/build_app.py first).
# Each source has no document skeleton (the artifact publisher adds one), so wrap() adds it.
# (source, package path, [(old, new)])
PAGES = [
    ("redesign/demo-app/app.html", "demo.html", []),
]
FOLDERS = [("contracts", "engine/contracts"), ("replay", "engine/replay"), ("preds", "engine/preds"), ("evals", "engine/evals")]

# Markdown notes whose links point at working-folder names. (source, package path, [(old, new)])
NOTES = [
    ("ANNEX_ASSUMPTIONS.md", "notes/assumptions-and-implementation.md", [
        ("(CASE_STUDY.md)", "(../case-study.html)"),
        ("(discovery/process_discovery_workbook.xlsx)", "(../discovery/process-discovery-workbook.xlsx)"),
        ("in `playbook.yaml`", "in `engine/playbook.yaml`"),
        ("Score `preds/`", "Score `engine/preds/`"),
    ]),
    ("TALK_TRACK.md", "notes/talk-track.md", [
        ("The audience gets `CASE_STUDY.md`.", "The audience gets `case-study.html`."),
    ]),
]

def wrap(page):
    """Add the document skeleton that the artifact publisher adds: doctype, metas and the same small reset."""
    head_end = page.index("</style>") + len("</style>")
    head, body = page[:head_end], page[head_end:]
    metas = ""
    if "charset=" not in head:
        metas += '<meta charset="utf-8">\n'
    if 'name="viewport"' not in head:
        metas += '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    reset = ('<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
             'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n')
    return ('<!doctype html>\n<html lang="en">\n<head>\n' + metas + reset + head.strip() + '\n</head>\n<body>\n'
            + body.strip() + '\n</body>\n</html>\n')


def put(rel, data):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)


def main():
    # Empty the folder but keep it, so a preview server that serves it can stay running.
    os.makedirs(OUT, exist_ok=True)
    for entry in os.listdir(OUT):
        p = os.path.join(OUT, entry)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for src, dst in FILES:
        p = os.path.join(OUT, dst)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        shutil.copyfile(os.path.join(HERE, src), p)
    for src, dst in FOLDERS:
        shutil.copytree(os.path.join(HERE, src), os.path.join(OUT, dst), ignore=shutil.ignore_patterns("__pycache__"))
    for src, dst, swaps in NOTES:
        text = open(os.path.join(HERE, src), encoding="utf-8").read()
        for old, new in swaps:
            if old not in text:
                raise SystemExit("%s no longer contains: %s" % (src, old))
            text = text.replace(old, new)
        put(dst, text)
    for src, dst, swaps in PAGES:
        page = open(os.path.join(HERE, src), encoding="utf-8").read()
        for old, new in swaps:
            if old not in page:
                raise SystemExit("%s no longer contains: %s" % (src, old))
            page = page.replace(old, new)
        put(dst, wrap(page))

    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(OUT):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.join(NAME, os.path.relpath(full, OUT)))
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print("wrote %s: %d files, %d KB" % (ZIP, n, os.path.getsize(ZIP) // 1024))


if __name__ == "__main__":
    main()
