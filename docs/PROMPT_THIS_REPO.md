# Prompt This Repo

Use this repo as the MDA page compiler, not as a generic static-site generator.

Mission:
Build pages from Markdown plus manifest YAML. The manifest chooses roles and slots. Templates place slots. CSS styles them. The validator tries to break the result before anything becomes production.

Rules:
- Do not hand-edit generated HTML in `output/` as the source of truth.
- Edit `content/*.md`, `manifests/*.yml`, `layouts/`, `partials/`, `assets/`, or `config/`.
- Add new semantic blocks in `config/block_map.yml`.
- Add new production rules in `scripts/validate_page.py`.
- Keep `brand: The Moral Decline of America`; reject old "Moral Decay" language.
- Keep `asset_id`/filename separate from public reader order if ordering is added later.
- `status: production` is allowed only after `python scripts/publish_gate.py` passes.

Desired pipeline:

```txt
Markdown/frontmatter
-> semantic block parser
-> manifest slot resolver
-> Jinja layout + partials
-> generated HTML
-> QA validator
-> publish gate
```

When extending the repo, preserve the core architecture:

```txt
Markdown chooses components.
Templates place components.
CSS styles components.
Scripts connect and reject bad output.
```
