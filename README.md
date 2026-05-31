# MDA Site Compiler

Custom static-page compiler for The Moral Decline of America / Theophysics HTML pages.

This is intentionally **not** an out-of-the-box site generator. It is a small, modifiable build system that lets you:

- Write source pages in Markdown with YAML frontmatter.
- Choose layout slots: topbar, hero, nav, sidebar, footer, audio, proof layer, related ring.
- Use custom semantic blocks like `::definition`, `::claim`, `::proof`, `::audit`, `::quote`.
- Compile into your own custom HTML templates and partials.
- Run a QA gate before marking pages as production.
- Keep compiler behavior editable through `config/block_map.yml` and `config/manifest_schema.yml`.
- Run the same publish gate locally and in GitHub Actions.

## Folder map

```txt
content/              Markdown source pages
manifests/            Optional per-page YAML manifests
layouts/              Full-page HTML shells
partials/             Reusable page components
assets/css/           Shared CSS
assets/js/            Shared JavaScript
scripts/              Build and validation scripts
config/               Semantic block map and manifest schema
docs/                 Repo prompting and handoff notes
.github/workflows/    CI publish gate
output/               Generated site files
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Build one page

```bash
python scripts/build_page.py content/MDA-050-jacob-2025.md
```

## Validate manifest or generated HTML

```bash
python scripts/validate_page.py manifests/MDA-050-jacob-2025.yml
python scripts/validate_page.py output/moral-decline/MDA-050-jacob-2025.html
```

## Build all pages and apply publish gate

```bash
python scripts/publish_gate.py
```

## Core idea

Markdown does not control every visual detail. Markdown/frontmatter chooses **roles and slots**.

Example:

```yaml
layout: article
topbar: main
hero: blackboard
nav: mda
sidebar: toc
footer: standard
audio: true
proof_layer: hidden
related_ring: hidden
status: audit
```

The compiler loads those partials, places them into the layout, renders content, and validates the final HTML.

## Production rule

A page should only be marked `status: production` if the validator passes.

Production pages are rejected if the generated HTML contains known corruption markers, old "Moral Decay" branding, old part labels, duplicate topbars, duplicate audio assets, placeholder related-work panels, or mismatched canonical URLs.

## Semantic blocks

Semantic block rendering is controlled by `config/block_map.yml`.

Example:

```yaml
lean:
  tag: pre
  class: lean-proof-block
  label: Lean Surface
```

Then Markdown can use:

```md
::lean
theorem sample : True := by
  trivial
::
```

This is the main extension point. Do not bury new page logic inside random Markdown conventions.

## GitHub template use

This repo is ready to push as a GitHub repository. The included workflow runs:

```bash
python scripts/publish_gate.py
```

That means every pull request has to build the Markdown, validate manifests, validate generated HTML, and fail before broken pages can be promoted.

For AI handoff, start with `docs/PROMPT_THIS_REPO.md`.


## GUI mode

Run the local no-code builder:

```bash
streamlit run gui_app.py
```

The GUI lets you:

- create/open Markdown pages
- fill page metadata with forms
- choose topbar, hero, nav, sidebar, footer from dropdowns
- toggle audio, audit/proof layer, and related-work ring
- set colors and widths with GUI controls
- save the manifest automatically
- build the final HTML
- run validation and publish gate
- preview the generated page

The GUI writes normal files into `content/` and `manifests/`, so you can still edit everything by hand later if needed.
