# GUI Part System

The GUI should be built over the AI-readable contracts, not beside them.

The working model is:

```txt
Markdown / existing HTML
-> structure labels
-> component manifest
-> page part controls
-> compiler
-> validator
-> publish gate
```

The GUI is a visual control surface for the same manifests an AI partner can edit directly.

## The 12 Parts

Most pages can be described by twelve editable page systems:

1. Page Identity
2. Top Bar
3. Hero
4. Navigation
5. Sidebar
6. Body Content
7. Images
8. Proof/Audit Layer
9. Reader Modes
10. Audio/Media
11. Related Ring
12. Footer

The 13th surface is not a page part. It is the QA / Publish Gate that checks all parts together.

The machine-readable registry lives at:

```txt
config/gui_part_registry.yml
```

## How It Should Feel

The left side of the GUI can show the page parts:

```txt
Identity
Top Bar
Hero
Navigation
Sidebar
Body
Images
Proof Layer
Reader Modes
Media
Related Ring
Footer
QA
```

Selecting one part opens a right-side panel with the controls for that part.

Example for Images:

```txt
source
alt
placement
align
width
height
caption
crop
mobile_behavior
```

Example for Header/Hero:

```txt
hero component
title
subtitle
claim badge
background image
alignment
color theme
```

The GUI should not invent a second data model. It edits:

```txt
manifests/*.yml
component_manifests/*.components.yml
config/*.yml
```

## Script Harmony

Legacy scripts are not random extras. Each one should belong to one page part or to QA.

Examples:

- `hero_image_audit.py` belongs to Hero and Images.
- `wire_mda_navigation.py` belongs to Navigation.
- `mda_proof_layer_inject.py` belongs to Proof/Audit Layer.
- `mda_audio_catalog_map.py` belongs to Audio/Media.
- `mda_audit_repair.py` belongs to QA / Publish Gate.

Some scripts cover several parts. That is fine. The registry names where each script belongs.

## AI-First Rule

Build the CLI/manifest path first:

```txt
detect -> manifest -> build -> validate
```

Then put the GUI over it:

```txt
select part -> edit manifest controls -> rebuild preview -> validate
```

This prevents the GUI from becoming another one-off tool. It also lets AI partners work through the same structure without clicking buttons.

## No-Loss Import

When Markdown is imported, structure detection should label the parts:

```txt
# Title -> heading_001 / identity title candidate
![image](...) -> image_001
::proof -> proof_layer block
::quote -> quote block
```

The goal is no loss between source Markdown, component manifest, and generated HTML.

If the detector is uncertain, it should mark the component as `review_needed` instead of guessing silently.
