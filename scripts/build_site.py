#!/usr/bin/env python3
"""Build a static, Vercel-friendly site from profile + generated posts."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "config" / "author_profile.md"
POSTS_DIR = ROOT / "generated_posts"
SITE_DIR = ROOT / "site"


def md_line_to_html(line: str) -> str:
    line = line.rstrip()
    if not line:
        return ""
    escaped = html.escape(line)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a class="text-cyan-400" href="\2">\1</a>', escaped)
    if line.startswith("### "):
        return f"<h3>{html.escape(line[4:])}</h3>"
    if line.startswith("## "):
        return f"<h2>{html.escape(line[3:])}</h2>"
    if line.startswith("# "):
        return f"<h1>{html.escape(line[2:])}</h1>"
    if line.startswith("- "):
        return f"<li>{escaped[2:]}</li>"
    return f"<p>{escaped}</p>"


def markdown_to_html(raw: str) -> str:
    lines = raw.splitlines()
    output = []
    in_list = False
    for line in lines:
        line_html = md_line_to_html(line)
        if line.startswith("- ") and not in_list:
            output.append("<ul>")
            in_list = True
        if not line.startswith("- ") and in_list:
            output.append("</ul>")
            in_list = False
        if line_html:
            output.append(line_html)
    if in_list:
        output.append("</ul>")
    return "\n".join(output)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    meta_raw = parts[1]
    content = parts[2].strip()
    meta = {}
    for line in meta_raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, content


def shell_html(title: str, body: str) -> str:
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"UTF-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
<title>{html.escape(title)}</title><script src=\"https://cdn.tailwindcss.com\"></script></head>
<body class=\"min-h-screen bg-slate-950 text-slate-100\">{body}</body></html>"""


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    blog_dir = SITE_DIR / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    profile_raw = PROFILE_PATH.read_text(encoding="utf-8") if PROFILE_PATH.exists() else "# Your Name"
    profile_html = markdown_to_html(profile_raw)

    posts = []
    for path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        meta, content = parse_frontmatter(path.read_text(encoding="utf-8"))
        posts.append({
            "slug": path.stem,
            "title": meta.get("title") or path.stem,
            "summary": meta.get("summary", "Generated AI blog post"),
            "date": meta.get("date", ""),
            "html": markdown_to_html(content),
        })

    cards = "".join(
        f'<a href="/blog/{p["slug"]}.html" class="block rounded-2xl border border-slate-800 bg-slate-900 p-6 hover:border-cyan-400"><p class="text-sm text-slate-400">{p["date"]}</p><h3 class="mt-2 text-xl font-semibold">{html.escape(p["title"])}</h3><p class="mt-2 text-slate-300">{html.escape(p["summary"])}</p></a>'
        for p in posts
    )
    if not cards:
        cards = '<p class="text-slate-400">No posts yet. Add a draft to blog_drafts/ and run the workflow.</p>'

    index = f'<main class="mx-auto max-w-6xl p-6 md:p-10"><header class="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl"><p class="text-cyan-400">Open Source AI Blog Generator</p><div class="prose prose-invert mt-4 max-w-none">{profile_html}</div></header><section class="mt-10"><h2 class="text-2xl font-bold">Published Posts</h2><div class="mt-4 grid gap-4 md:grid-cols-2">{cards}</div></section></main>'
    (SITE_DIR / "index.html").write_text(shell_html("AI Blog Generator", index), encoding="utf-8")

    for post in posts:
        body = f'<main class="mx-auto max-w-3xl p-6 md:p-10"><a class="text-cyan-400" href="/index.html">← Back</a><article class="prose prose-invert mt-6 max-w-none rounded-3xl border border-slate-800 bg-slate-900 p-8"><h1>{html.escape(post["title"])}</h1><p class="text-slate-400">{post["date"]}</p>{post["html"]}</article></main>'
        safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "", post["slug"])
        (blog_dir / f"{safe_slug}.html").write_text(shell_html(post["title"], body), encoding="utf-8")


if __name__ == "__main__":
    build()
