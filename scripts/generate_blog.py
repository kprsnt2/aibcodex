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
    base_url: str


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
    """Resolve provider from AI_PROVIDER or auto-detect from available API keys."""
    forced = os.getenv("AI_PROVIDER", "").strip().lower()

    openai_key = os.getenv("OPENAI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    claude_key = os.getenv("CLAUDE_API_KEY", "")

    mapping = {
        "openai": ProviderConfig(
            "openai",
            os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_key,
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        ),
        "openrouter": ProviderConfig(
            "openrouter",
            os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            openrouter_key,
            os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        ),
        "nvidia": ProviderConfig(
            "nvidia",
            os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
            nvidia_key,
            os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        ),
        "gemini": ProviderConfig(
            "gemini",
            os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            gemini_key,
            "https://generativelanguage.googleapis.com/v1beta",
        ),
        "claude": ProviderConfig(
            "claude",
            os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            claude_key,
            "https://api.anthropic.com/v1",
        ),
    }

    if forced:
        if forced not in mapping:
            raise ValueError("Unsupported AI_PROVIDER. Use openai/openrouter/nvidia/gemini/claude")
        config = mapping[forced]
        if not config.api_key:
            raise RuntimeError(f"Missing key for forced provider '{forced}'")
        return config

    for name in ["openai", "openrouter", "nvidia", "gemini", "claude"]:
        if mapping[name].api_key:
            return mapping[name]

    raise RuntimeError(
        "No API key configured. Set one key: OPENAI_API_KEY or OPENROUTER_API_KEY or NVIDIA_API_KEY "
        "(gemini/claude also supported)."
    )


def build_prompt(profile_md: str, draft_md: str, draft_filename: str) -> str:
    return f"""
You are an expert technical blog writer.
Create a publication-ready markdown blog post using profile + draft `{draft_filename}`.

Rules:
- Keep factual claims tied to provided draft data.
- If draft references images/charts/videos, include them naturally in markdown.
- Include: compelling intro, table of contents, practical sections, failures/lessons, conclusion.
- Keep paragraphs short and clear.
- Return ONLY markdown with valid frontmatter:
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
    with request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_with_openai_compatible(config: ProviderConfig, prompt: str) -> str:
    payload = {
        "model": config.model,
        "temperature": 0.4,
        "messages": [
            {"role": "system", "content": "You write high-quality technical blog posts in markdown."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {"authorization": f"Bearer {config.api_key}"}

    if config.name == "openrouter":
        headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL", "https://example.com")
        headers["X-Title"] = os.getenv("OPENROUTER_APP_NAME", "Open AI Blog Generator")

    data = http_post_json(f"{config.base_url}/chat/completions", payload, headers)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No response choices returned from provider")
    return choices[0].get("message", {}).get("content", "").strip()


def generate_with_gemini(config: ProviderConfig, prompt: str) -> str:
    url = f"{config.base_url}/models/{config.model}:generateContent?key={config.api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4}}
    data = http_post_json(url, payload, {})
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(part.get("text", "") for part in parts).strip()


def generate_with_claude(config: ProviderConfig, prompt: str) -> str:
    payload = {
        "model": config.model,
        "max_tokens": 2200,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = http_post_json(
        f"{config.base_url}/messages",
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

    if provider.name in {"openai", "openrouter", "nvidia"}:
        raw = generate_with_openai_compatible(provider, prompt)
    elif provider.name == "gemini":
        raw = generate_with_gemini(provider, prompt)
    else:
        raw = generate_with_claude(provider, prompt)

    post = ensure_frontmatter(raw, title=title, draft_source=str(draft_path))

    if args.dry_run:
        print(post)
        return

    output_path = write_post(Path(args.outdir), title, post)
    print(json.dumps({"generated_post": str(output_path), "provider": provider.name, "model": provider.model}))


if __name__ == "__main__":
    main()
