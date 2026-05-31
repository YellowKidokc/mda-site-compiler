from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "component_manifests"
SCHEMA_PATH = ROOT / "config" / "component_schema.yml"


@dataclass
class Component:
    id: str
    type: str
    role: str
    source: dict[str, Any]
    controls: dict[str, Any] = field(default_factory=dict)
    lock: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def load_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        return {}
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8")) or {}


def split_frontmatter(text: str) -> tuple[dict[str, Any], str, int]:
    if not text.startswith("---"):
        return {}, text, 0
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text, 0
    offset_lines = text[: match.start(2)].count("\n")
    return yaml.safe_load(match.group(1)) or {}, match.group(2), offset_lines


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def component_id(kind: str, counters: dict[str, int]) -> str:
    counters[kind] = counters.get(kind, 0) + 1
    return f"{kind}_{counters[kind]:03d}"


def defaults_for(kind: str, schema: dict[str, Any]) -> dict[str, Any]:
    return dict((schema.get("defaults") or {}).get(kind, {}))


def line_number(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def section_context(lines: list[str], index: int) -> str:
    for cursor in range(index, -1, -1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", lines[cursor])
        if match:
            return slug(match.group(2))
    return "document-start"


def label_markdown(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body, line_offset = split_frontmatter(raw)
    lines = body.splitlines()
    counters: dict[str, int] = {}
    components: list[Component] = []

    semantic_re = re.compile(r"^::(?P<kind>\w+)(?P<attrs>[^\n]*)\n(?P<body>.*?)\n::\s*$", re.MULTILINE | re.DOTALL)
    claimed_ranges: list[range] = []

    for match in semantic_re.finditer(body):
        kind = match.group("kind")
        body_start_line = line_number(body, match.start())
        body_end_line = line_number(body, match.end())
        start_line = body_start_line + line_offset
        end_line = body_end_line + line_offset
        claimed_ranges.append(range(body_start_line, body_end_line + 1))
        role = "quote" if kind == "quote" else "semantic_block"
        controls = defaults_for("semantic_block", schema)
        controls.update(
            {
                "block_type": kind,
                "placement": f"after:{section_context(lines, body_start_line - 1)}",
                "visibility": "visible",
            }
        )
        components.append(
            Component(
                id=component_id(role, counters),
                type=role,
                role=kind,
                source={"format": "markdown", "path": str(path.relative_to(ROOT)), "line_start": start_line, "line_end": end_line},
                controls=controls,
                lock={"content": False, "role": False},
            )
        )

    for i, line in enumerate(lines, start=1):
        if any(i in item for item in claimed_ranges):
            continue
        source_line = i + line_offset

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            text = heading.group(2).strip()
            components.append(
                Component(
                    id=component_id("heading", counters),
                    type="heading",
                    role="section_heading",
                    source={"format": "markdown", "path": str(path.relative_to(ROOT)), "line_start": source_line, "line_end": source_line},
                    controls={"level": len(heading.group(1)), "text": text, "anchor": slug(text), "placement": "document_flow"},
                    lock={"text": False, "level": False},
                )
            )
            continue

        image = re.search(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+\"(?P<title>[^\"]*)\")?\)", line)
        if image:
            controls = defaults_for("image", schema)
            controls.update(
                {
                    "source": image.group("src"),
                    "alt": image.group("alt"),
                    "caption": image.group("title") or "auto",
                    "placement": f"after:{section_context(lines, i - 1)}",
                }
            )
            components.append(
                Component(
                    id=component_id("image", counters),
                    type="image",
                    role="article_image",
                    source={"format": "markdown", "path": str(path.relative_to(ROOT)), "line_start": source_line, "line_end": source_line},
                    controls=controls,
                    lock={"source": False, "alt": False, "placement": False},
                )
            )
            continue

        if line.strip() and not line.lstrip().startswith(("-", "*", ">")):
            components.append(
                Component(
                    id=component_id("paragraph", counters),
                    type="paragraph",
                    role="body_copy",
                    source={"format": "markdown", "path": str(path.relative_to(ROOT)), "line_start": source_line, "line_end": source_line},
                    controls={"placement": f"in:{section_context(lines, i - 1)}", **defaults_for("paragraph", schema)},
                    lock={"content": False},
                )
            )

    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(path.relative_to(ROOT)),
        "frontmatter": frontmatter,
        "components": [
            component.__dict__
            for component in sorted(components, key=lambda item: item.source.get("line_start", 0))
        ],
    }


def label_html(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    counters: dict[str, int] = {}
    components: list[Component] = []

    selectors = [
        ("header", "html_component", "topbar"),
        ("nav", "html_component", "navigation"),
        ("section[class*=hero]", "html_component", "hero"),
        ("aside", "html_component", "sidebar"),
        ("footer", "html_component", "footer"),
    ]
    for selector, kind, role in selectors:
        for node in soup.select(selector):
            if not isinstance(node, Tag):
                continue
            components.append(
                Component(
                    id=component_id(role, counters),
                    type=kind,
                    role=role,
                    source={"format": "html", "path": str(path.relative_to(ROOT)), "selector": selector},
                    controls={
                        "tag": node.name,
                        "id": node.get("id", ""),
                        "classes": node.get("class", []),
                        "placement": "template_slot",
                        "visibility": "visible",
                    },
                    lock={"role": True},
                )
            )

    for image in soup.find_all("img"):
        controls = defaults_for("image", schema)
        controls.update(
            {
                "source": image.get("src", ""),
                "alt": image.get("alt", ""),
                "width": image.get("width", controls.get("width", "auto")),
                "height": image.get("height", controls.get("height", "auto")),
                "placement": "html_flow",
            }
        )
        components.append(
            Component(
                id=component_id("image", counters),
                type="image",
                role="article_image",
                source={"format": "html", "path": str(path.relative_to(ROOT)), "tag": "img"},
                controls=controls,
                lock={"source": False, "alt": False, "placement": False},
            )
        )

    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(path.relative_to(ROOT)),
        "components": [component.__dict__ for component in components],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Label Markdown or HTML as editable page components.")
    parser.add_argument("source", help="Markdown or HTML file to label.")
    parser.add_argument("--out", help="Output component manifest path.")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    schema = load_schema()

    if source.suffix.lower() in {".md", ".markdown"}:
        manifest = label_markdown(source, schema)
    elif source.suffix.lower() in {".html", ".htm"}:
        manifest = label_html(source, schema)
    else:
        raise SystemExit(f"Unsupported source type: {source.suffix}")

    COMPONENT_DIR.mkdir(exist_ok=True)
    out = Path(args.out) if args.out else COMPONENT_DIR / f"{source.stem}.components.yml"
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Labeled {len(manifest['components'])} components -> {out}")


if __name__ == "__main__":
    main()
