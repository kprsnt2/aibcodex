#!/usr/bin/env python3
"""Generate polished blog posts from analysis drafts using an LLM provider."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


@dataclass
class ProviderConfig:
    name: str
    model: str
    api_key: str


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8").strip()


def extract_title(draft_content: str, draft_path: Path) -> str:
    for line in draft_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("# ").strip()
    return draft_path.stem.replace("-", " ").title()


def slugify(value: str) -> str:
    keep = [ch.lower() if ch.isalnum() else "-" for ch in value]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "generated-post"


def provider_from_env() -> ProviderConfig:
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return ProviderConfig("gemini", os.getenv("GEMINI_MODEL", "gemini-1.5-pro"), os.getenv("GEMINI_API_KEY", ""))
    if provider == "claude":
        return ProviderConfig("claude", os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"), os.getenv("CLAUDE_API_KEY", ""))
    raise ValueError("AI_PROVIDER must be either 'gemini' or 'claude'")


def build_prompt(profile_md: str, draft_md: str, draft_filename: str) -> str:
    return f"""
You are an expert technical blog writer.
Create a publication-ready markdown blog post using profile + draft `{draft_filename}`.
Return ONLY markdown with valid frontmatter:
---
title:
summary:
date: YYYY-MM-DD
tags: [ai, blog]
draft_source:
---

## Author profile
{profile_md}

## Draft analysis
{draft_md}
""".strip()


def http_post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"content-type": "application/json", **headers}, method="POST")
    with request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_with_gemini(config: ProviderConfig, prompt: str) -> str:
    if not config.api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model}:generateContent?key={config.api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4}}
    data = http_post_json(url, payload, {})
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(part.get("text", "") for part in parts).strip()


def generate_with_claude(config: ProviderConfig, prompt: str) -> str:
    if not config.api_key:
        raise RuntimeError("Missing CLAUDE_API_KEY")
    payload = {
        "model": config.model,
        "max_tokens": 2200,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = http_post_json(
        "https://api.anthropic.com/v1/messages",
        payload,
        {"x-api-key": config.api_key, "anthropic-version": "2023-06-01"},
    )
    return "\n".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text").strip()


def ensure_frontmatter(output: str, title: str, draft_source: str) -> str:
    if output.startswith("---"):
        return output
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        f"---\ntitle: \"{title}\"\nsummary: \"AI-generated post from your analysis draft.\"\n"
        f"date: {today}\ntags: [ai, generated]\ndraft_source: {draft_source}\n---\n\n{output}\n"
    )


def write_post(output_dir: Path, title: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{slugify(title)}.md"
    out_path = output_dir / filename
    out_path.write_text(content.strip() + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate blog post from markdown drafts")
    parser.add_argument("--profile", default="config/author_profile.md")
    parser.add_argument("--draft", required=True)
    parser.add_argument("--outdir", default="generated_posts")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile_md = read_text(Path(args.profile))
    draft_path = Path(args.draft)
    draft_md = read_text(draft_path)

    title = extract_title(draft_md, draft_path)
    prompt = build_prompt(profile_md, draft_md, draft_path.name)
    provider = provider_from_env()
    raw = generate_with_gemini(provider, prompt) if provider.name == "gemini" else generate_with_claude(provider, prompt)
    post = ensure_frontmatter(raw, title=title, draft_source=str(draft_path))

    if args.dry_run:
        print(post)
        return

    output_path = write_post(Path(args.outdir), title, post)
    print(json.dumps({"generated_post": str(output_path)}))


if __name__ == "__main__":
    main()
