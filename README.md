# Open AI Blog Generator (Vercel-ready)

Turn raw analysis drafts into polished blog posts automatically.

## What this template does

1. You update your profile in `config/author_profile.md`.
2. You push a draft (`.md` or `.txt`) into `blog_drafts/`.
3. GitHub Actions calls Gemini or Claude to expand your draft into a complete post.
4. Generated markdown is saved into `generated_posts/`.
5. A static site is rebuilt into `site/` and can be deployed by Vercel.

## Repository structure

- `config/author_profile.md`: your identity, links, tone, and project context.
- `blog_drafts/`: incoming analysis docs with optional image/video references.
- `generated_posts/`: AI-written blog posts.
- `scripts/generate_blog.py`: LLM generation pipeline.
- `scripts/build_site.py`: static site builder with a shadcn-inspired dark UI style.
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
- You can include images/charts links in markdown
- You can include video links (Loom, YouTube, etc)

### 3) Configure GitHub secrets and variables

Add **one** provider:

#### Option A: Gemini
- Secret: `GEMINI_API_KEY`
- Variable: `AI_PROVIDER=gemini`
- Optional variable: `GEMINI_MODEL=gemini-1.5-pro`

#### Option B: Claude
- Secret: `CLAUDE_API_KEY`
- Variable: `AI_PROVIDER=claude`
- Optional variable: `CLAUDE_MODEL=claude-3-5-sonnet-20241022`

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

# Generate from a draft
AI_PROVIDER=gemini GEMINI_API_KEY=xxx python scripts/generate_blog.py --draft blog_drafts/sample-analysis.md

# Build static site
python scripts/build_site.py
```

## Improvements included over your original idea

- Provider abstraction (Gemini or Claude) via environment variables.
- Frontmatter enforcement for stable downstream rendering.
- Opinionated profile schema so contributors can plug-and-play quickly.
- Static export flow built for Vercel with no server required.
- Clean open-source starter structure for forks and community reuse.

## Suggested next upgrades

- Add multi-draft queue processing (generate one post per new draft).
- Add editorial guardrails (fact-checking and citation prompts).
- Add scheduled publishing + social auto-post hooks.
- Add issue templates and starter prompts for community submissions.
