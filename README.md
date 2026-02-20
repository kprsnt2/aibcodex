# Open AI Blog Generator (Vercel-ready)

Turn raw analysis drafts into polished blog posts automatically.

## What this template does

1. You update your profile in `config/author_profile.md`.
2. You push a draft (`.md` or `.txt`) into `blog_drafts/`.
3. GitHub Actions calls an AI provider (OpenAI/OpenRouter/NVIDIA/Gemini/Claude) to expand your draft into a complete post.
4. Generated markdown is saved into `generated_posts/`.
5. A polished static site is rebuilt into `site/` and deployed by Vercel.

## Repository structure

- `config/author_profile.md`: your identity, links, tone, and project context.
- `blog_drafts/`: incoming analysis docs with optional image/video references.
- `generated_posts/`: AI-written blog posts.
- `scripts/generate_blog.py`: multi-provider LLM generation pipeline.
- `scripts/build_site.py`: modern dark static site builder.
- `.github/workflows/ai-blog-pipeline.yml`: automation workflow.

## Quick start

### 1) Customize your profile

Edit `config/author_profile.md` with your:
- name and intro
- profession
- social links
- resume
- projects
- writing tone

### 2) Add a draft

Drop your analysis file into `blog_drafts/`:
- Supports `.md` and `.txt`
- Include images/charts references in markdown
- Include video links (Loom, YouTube, etc)

### 3) Configure **any one** API key

You only need one of these keys:

#### OpenAI (recommended)
- Secret: `OPENAI_API_KEY`
- Optional variable: `OPENAI_MODEL=gpt-4o-mini`

#### OpenRouter
- Secret: `OPENROUTER_API_KEY`
- Optional variable: `OPENROUTER_MODEL=openai/gpt-4o-mini`

#### NVIDIA NIM
- Secret: `NVIDIA_API_KEY`
- Optional variable: `NVIDIA_MODEL=meta/llama-3.1-70b-instruct`

#### Also supported
- Gemini: `GEMINI_API_KEY`
- Claude: `CLAUDE_API_KEY`

> Optional override: set `AI_PROVIDER` to explicitly force one provider. If omitted, the script auto-selects the first configured key.

### 4) Push to `main`

Any push affecting `blog_drafts/` triggers generation + build.

### 5) Deploy to Vercel

- Import repo in Vercel
- Framework preset: **Other**
- Output directory: `site` (already set in `vercel.json`)

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Auto-detect provider from any available key
OPENAI_API_KEY=xxx python scripts/generate_blog.py --draft blog_drafts/sample-analysis.md

# Or force one
AI_PROVIDER=openrouter OPENROUTER_API_KEY=xxx python scripts/generate_blog.py --draft blog_drafts/sample-analysis.md

# Build static site
python scripts/build_site.py
```

## Why this is better

- Any-one-key provider model: OpenAI/OpenRouter/NVIDIA (plus Gemini/Claude fallback).
- Better generated-site UI with improved layout, card design, and typography.
- Frontmatter enforcement for consistent rendering.
- Open-source starter structure optimized for forks and fast setup.

## Suggested next upgrades

- Multi-draft queue processing (generate one post per new draft).
- Editorial guardrails (fact-checking and citation checks).
- Scheduled publishing + social auto-post integrations.
- Advanced markdown rendering and tagging pages.
