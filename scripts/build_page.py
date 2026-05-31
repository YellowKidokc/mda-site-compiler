from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path
from typing import Any, Dict, Tuple

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://faiththruphysics.com"
BLOCK_MAP_PATH = ROOT / "config" / "block_map.yml"


def load_block_map() -> Dict[str, Dict[str, str]]:
    if not BLOCK_MAP_PATH.exists():
        raise FileNotFoundError(f"Missing block map: {BLOCK_MAP_PATH}")
    data = yaml.safe_load(BLOCK_MAP_PATH.read_text(encoding="utf-8")) or {}
    return data


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("Frontmatter starts with --- but does not close correctly.")
    meta = yaml.safe_load(match.group(1)) or {}
    return meta, match.group(2)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for key, value in re.findall(r'([\w-]+)="([^"]*)"', attr_text):
        attrs[key] = value
    return attrs


def render_semantic_blocks(md_text: str, block_map: Dict[str, Dict[str, str]]) -> str:
    pattern = re.compile(r"^::(\w+)([^\n]*)\n(.*?)\n::\s*$", re.MULTILINE | re.DOTALL)

    def repl(match: re.Match[str]) -> str:
        block_type = match.group(1)
        attr_text = match.group(2).strip()
        inner = match.group(3).strip()
        spec = block_map.get(block_type, {"tag": "section", "class": f"{block_type}-block", "label": block_type.title()})
        attrs = parse_attrs(attr_text)
        data_attrs = " ".join(f'data-{k}="{escape(v, quote=True)}"' for k, v in attrs.items())
        tag = spec["tag"]
        label = spec["label"]
        klass = f"semantic-block {spec['class']}"
        if tag == "pre":
            inner_html = f"<code>{escape(inner)}</code>"
        else:
            inner_html = markdown.markdown(inner, extensions=["extra"])
        return f'<{tag} class="{klass}" data-block="{block_type}" {data_attrs}>\n<p class="semantic-block-label">{label}</p>\n{inner_html}\n</{tag}>'

    return pattern.sub(repl, md_text)


def md_to_html(md_text: str) -> str:
    preprocessed = render_semantic_blocks(md_text, load_block_map())
    return markdown.markdown(preprocessed, extensions=["extra", "toc"], output_format="html5")


def build_toc(md_text: str) -> str:
    headings = re.findall(r"^(#{2,3})\s+(.+)$", md_text, re.MULTILINE)
    if not headings:
        return ""
    items = []
    for marks, title in headings:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        cls = "toc-h3" if len(marks) == 3 else "toc-h2"
        items.append(f'<li class="{cls}"><a href="#{slug}">{title}</a></li>')
    return "<ul>" + "\n".join(items) + "</ul>"


def load_partial(env: Environment, folder: str, name: str | bool | None, context: Dict[str, Any]) -> str:
    if not name or name == "hidden":
        return ""
    template_name = f"partials/{folder}/{name}.html"
    return env.get_template(template_name).render(**context)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/build_page.py content/PAGE.md")

    source = Path(sys.argv[1])
    if not source.is_absolute():
        source = ROOT / source
    raw = source.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(raw)

    manifest_path = ROOT / "manifests" / f"{source.stem}.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    meta = {**frontmatter, **(manifest or {})}

    env = Environment(loader=FileSystemLoader(ROOT), autoescape=select_autoescape(["html", "xml"]))
    meta["site_url"] = SITE_URL
    meta["content_html"] = md_to_html(body)
    meta["toc_html"] = build_toc(body)

    meta["topbar_html"] = load_partial(env, "topbars", meta.get("topbar"), meta)
    meta["nav_html"] = load_partial(env, "navs", meta.get("nav"), meta)
    meta["hero_html"] = load_partial(env, "heroes", meta.get("hero"), meta)
    meta["sidebar_html"] = load_partial(env, "sidebars", meta.get("sidebar"), meta) if meta.get("sidebar") else ""
    meta["footer_html"] = load_partial(env, "footers", meta.get("footer"), meta)

    layout = meta.get("layout", "article")
    html = env.get_template(f"layouts/{layout}.html").render(**meta)

    out_dir = ROOT / "output" / "moral-decline"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / meta.get("filename", f"{source.stem}.html")
    out_file.write_text(html, encoding="utf-8")
    print(f"Built {out_file}")


if __name__ == "__main__":
    main()
