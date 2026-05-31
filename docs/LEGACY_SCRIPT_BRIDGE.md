# Legacy Script Bridge

The legacy Master HTML scripts folder is the field workshop:

```txt
\\dlowenas\HPWorkstation\Desktop\Master HTMl\Scripts
```

This repository is the clean control surface:

```txt
detector -> manifest -> compiler -> validator -> GUI
```

They should harmonize, but they should not be merged blindly.

## Rule

Do not bulk-copy the legacy scripts into this repo.

Instead, harvest stable contracts:

- what the script reads
- what it writes
- what it refuses to touch
- how it proves the operation worked
- which manifest/report shape it should emit

The machine-readable bridge lives at:

```txt
config/legacy_script_bridge.yml
```

## Layer Map

### Scanners

Scripts such as `bootstrap_master_html_labels.py`, `hero_image_audit.py`, and `mda_media_manifest.py` belong near the detector/component-manifest layer. They teach the repo how to see pages, images, audio, and series identity.

### Validators

`mda_audit_repair.py` is the strongest validator source. Its production write behavior should stay legacy for now, but its checks should be extracted gradually:

- metadata
- canonical path
- encoding/mojibake
- local references
- shared assets
- analytics
- template names
- palette rules

### Transformers

`convert_html_to_clean_markdown.py` and `html_to_markdown_scrape.py` belong in the source-transformer layer. They are relevant when old HTML needs to become source Markdown or component manifests.

### Injectors

`component_swap.py`, `mda_proof_layer_inject.py`, `mda_reader_tabs_v2_patch.py`, and navigation wiring scripts should inform compiler components. Their future form should be manifest-driven rather than manual patch-driven.

### Media

Audio/player scripts should become media manifest contracts. Pages should not carry duplicate player CSS or JS because the compiler should know whether audio is enabled.

### Runner

`master_html_modular_runner.py` is the pattern to preserve:

```txt
list modules
run one narrow pass
default to report-only
write machine-readable outputs
require explicit apply for edits
```

## AI-First Direction

Build the CLI and manifest contracts first:

```txt
label_structure.py
component_manifests/*.components.yml
build_page.py
validate_page.py
publish_gate.py
```

Then put the GUI over those contracts.

The GUI should edit the same manifests an AI partner can edit directly. If the GUI hides structure instead of exposing it, the system drifts back into page soup.

## Next Practical Ports

1. Extract validator rules from `mda_audit_repair.py` into `scripts/validate_page.py`.
2. Make `build_page.py` consume `component_manifests/*.components.yml` for image controls.
3. Add a runner that executes detector -> manifest validation -> build -> QA report.
4. Add GUI controls for component manifests after the CLI path is stable.
