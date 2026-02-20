#!/usr/bin/env python3
"""Build a polished static, Vercel-friendly site from profile + generated posts."""

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

    if line.startswith("![") and "](" in line and line.endswith(")"):
        alt = line[2:line.index("]")]
        src = line[line.index("(") + 1 : -1]
        return (
            '<figure class="my-6 overflow-hidden rounded-xl border border-slate-700/70">'
            f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" class="w-full" />'
            f'<figcaption class="px-4 py-2 text-sm text-slate-400">{html.escape(alt)}</figcaption></figure>'
        )

    escaped = html.escape(line)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a class="text-cyan-300 underline" href="\2">\1</a>', escaped)

    if line.startswith("### "):
        return f"<h3>{html.escape(line[4:])}</h3>"
    if line.startswith("## "):
        return f"<h2>{html.escape(line[3:])}</h2>"
    if line.startswith("# "):
        return f"<h1>{html.escape(line[2:])}</h1>"
    if line.startswith("- "):
        return f"<li>{escaped[2:]}</li>"
    if re.match(r"^\d+\.\s+", line):
        item = re.sub(r"^\d+\.\s+", "", escaped)
        return f"<li>{item}</li>"
    return f"<p>{escaped}</p>"


def markdown_to_html(raw: str) -> str:
    lines = raw.splitlines()
    output = []
    in_ul = False
    in_ol = False

    for line in lines:
        is_ul = line.startswith("- ")
        is_ol = bool(re.match(r"^\d+\.\s+", line))

        if is_ul and not in_ul:
            if in_ol:
                output.append("</ol>")
                in_ol = False
            output.append("<ul>")
            in_ul = True
        if is_ol and not in_ol:
            if in_ul:
                output.append("</ul>")
                in_ul = False
            output.append("<ol>")
            in_ol = True
        if not is_ul and in_ul:
            output.append("</ul>")
            in_ul = False
        if not is_ol and in_ol:
            output.append("</ol>")
            in_ol = False

        line_html = md_line_to_html(line)
        if line_html:
            output.append(line_html)

    if in_ul:
        output.append("</ul>")
    if in_ol:
        output.append("</ol>")

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
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{html.escape(title)}</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
  <style>
    .glass {{ backdrop-filter: blur(8px); }}
    .prose h1 {{ font-size: 2rem; font-weight: 800; margin-top: 1rem; margin-bottom: .75rem; }}
    .prose h2 {{ font-size: 1.4rem; font-weight: 700; margin-top: 1.2rem; margin-bottom: .6rem; }}
    .prose h3 {{ font-size: 1.1rem; font-weight: 700; margin-top: 1rem; margin-bottom: .4rem; }}
    .prose p {{ color: #d1d5db; line-height: 1.75; margin: .65rem 0; }}
    .prose ul, .prose ol {{ margin: .8rem 0 .8rem 1.1rem; color: #d1d5db; }}
    .prose li {{ margin: .2rem 0; }}
  </style>
</head>
<body class=\"min-h-screen bg-slate-950 text-slate-100\">{body}</body>
</html>"""


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    blog_dir = SITE_DIR / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    profile_raw = PROFILE_PATH.read_text(encoding="utf-8") if PROFILE_PATH.exists() else "# Your Name"
    profile_html = markdown_to_html(profile_raw)

    posts = []
    for path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        meta, content = parse_frontmatter(path.read_text(encoding="utf-8"))
        posts.append(
            {
                "slug": path.stem,
                "title": meta.get("title") or path.stem,
                "summary": meta.get("summary", "Generated AI blog post"),
                "date": meta.get("date", ""),
                "html": markdown_to_html(content),
            }
        )

    cards = "".join(
        f'<a href="/blog/{p["slug"]}.html" class="group block rounded-2xl border border-slate-700/60 bg-slate-900/70 p-6 transition hover:-translate-y-0.5 hover:border-cyan-400/70 hover:shadow-[0_0_24px_rgba(34,211,238,0.2)]">'
        f'<p class="text-xs uppercase tracking-wider text-cyan-300/80">{p["date"] or "Draft"}</p>'
        f'<h3 class="mt-2 text-xl font-semibold text-white group-hover:text-cyan-100">{html.escape(p["title"])}</h3>'
        f'<p class="mt-3 text-sm leading-6 text-slate-300">{html.escape(p["summary"])}</p>'
        '<p class="mt-5 text-sm text-cyan-300">Read article →</p>'
        '</a>'
        for p in posts
    )

    if not cards:
        cards = '<p class="rounded-xl border border-dashed border-slate-700 p-6 text-slate-400">No posts yet. Add a draft to <code>blog_drafts/</code> and run the workflow.</p>'

    index = f"""
    <div class=\"pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.15),transparent_34%),radial-gradient(circle_at_80%_0%,rgba(168,85,247,0.12),transparent_26%)]\"></div>
    <main class=\"mx-auto max-w-6xl p-6 md:p-10\">
      <section class=\"glass overflow-hidden rounded-3xl border border-slate-700/70 bg-slate-900/65 p-8 shadow-2xl\">
        <p class=\"inline-flex rounded-full border border-cyan-400/40 bg-cyan-400/10 px-3 py-1 text-xs font-medium tracking-wide text-cyan-300\">Open Source AI Blog Generator</p>
        <h1 class=\"mt-4 text-4xl font-black tracking-tight\">Ship AI-written blogs from your raw analysis notes.</h1>
        <p class=\"mt-3 max-w-3xl text-slate-300\">Drop a markdown/text draft, trigger GitHub Actions, and auto-publish polished posts to a Vercel-ready static site.</p>
        <div class=\"prose mt-8 max-w-none\">{profile_html}</div>
      </section>

      <section class=\"mt-10\">
        <div class=\"mb-4 flex items-center justify-between\">
          <h2 class=\"text-2xl font-bold\">Published Posts</h2>
          <span class=\"rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400\">{len(posts)} total</span>
        </div>
        <div class=\"grid gap-4 md:grid-cols-2\">{cards}</div>
      </section>
    </main>
    """
    (SITE_DIR / "index.html").write_text(shell_html("AI Blog Generator", index), encoding="utf-8")

    for post in posts:
        body = f"""
        <div class=\"pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_0%_10%,rgba(56,189,248,0.10),transparent_38%),radial-gradient(circle_at_100%_0%,rgba(168,85,247,0.10),transparent_30%)]\"></div>
        <main class=\"mx-auto max-w-3xl p-6 md:p-10\">
          <a class=\"inline-flex rounded-full border border-slate-700 px-3 py-1 text-sm text-cyan-300 hover:border-cyan-400\" href=\"/index.html\">← Back to home</a>
          <article class=\"prose mt-6 rounded-3xl border border-slate-700/60 bg-slate-900/75 p-8 shadow-2xl\">
            <h1>{html.escape(post['title'])}</h1>
            <p class=\"text-slate-400\">{post['date']}</p>
            {post['html']}
          </article>
        </main>
        """
        safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "", post["slug"])
        (blog_dir / f"{safe_slug}.html").write_text(shell_html(post["title"], body), encoding="utf-8")


if __name__ == "__main__":
    build()
