from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
MANIFEST_DIR = ROOT / "manifests"
OUTPUT_DIR = ROOT / "output" / "moral-decline"
PARTIALS_DIR = ROOT / "partials"

st.set_page_config(page_title="MDA HTML Builder", layout="wide")


def list_names(folder: str) -> list[str]:
    path = PARTIALS_DIR / folder
    if not path.exists():
        return ["hidden"]
    names = [p.stem for p in sorted(path.glob("*.html"))]
    return ["hidden"] + names


def load_manifest(stem: str) -> Dict[str, Any]:
    path = MANIFEST_DIR / f"{stem}.yml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def save_manifest(stem: str, data: Dict[str, Any]) -> Path:
    MANIFEST_DIR.mkdir(exist_ok=True)
    path = MANIFEST_DIR / f"{stem}.yml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def default_markdown(title: str) -> str:
    return f"""---
title: "{title}"
---

# {title}

Opening paragraph goes here.

## First Section

Write the article section here.

::claim type="structural"
This is a claim block. The compiler will place it in the correct HTML wrapper.
::

::audit
Use this area for claim status, evidence notes, or audit comments.
::
"""


def slugify_title(title: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or "untitled"


def run_command(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout


def read_html_preview(path: Path) -> str:
    if not path.exists():
        return ""
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    return str(body) if body else html


def color_style_css(theme: Dict[str, str]) -> str:
    return """:root {
  --bg: %(bg)s;
  --panel: %(panel)s;
  --text: %(text)s;
  --muted: %(muted)s;
  --line: %(line)s;
  --accent: %(accent)s;
  --content-max: %(content_max)s;
  --sidebar-width: %(sidebar_width)s;
}
""" % theme

st.title("MDA HTML Builder GUI")
st.caption("Choose page parts with dropdowns, edit content, build HTML, and run the QA gate without touching command line.")

CONTENT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

existing_pages = sorted(CONTENT_DIR.glob("*.md"))
page_options = [p.name for p in existing_pages] + ["+ Create new page"]

with st.sidebar:
    st.header("Page")
    selected = st.selectbox("Open page", page_options)
    creating = selected == "+ Create new page"

    if creating:
        new_title = st.text_input("New page title", "New MDA Page")
        new_stem = st.text_input("File stem", slugify_title(new_title))
        source_path = CONTENT_DIR / f"{new_stem}.md"
        stem = new_stem
        if st.button("Create page"):
            if source_path.exists():
                st.error("That page already exists.")
            else:
                source_path.write_text(default_markdown(new_title), encoding="utf-8")
                st.success(f"Created {source_path.name}. Reload/select it from the dropdown.")
                st.stop()
    else:
        source_path = CONTENT_DIR / selected
        stem = source_path.stem

if creating and not source_path.exists():
    st.info("Create a page first, then the builder controls will appear.")
    st.stop()

raw_md = source_path.read_text(encoding="utf-8")
manifest = load_manifest(stem)

left, right = st.columns([0.56, 0.44], gap="large")

with left:
    st.subheader("1. Page identity")
    c1, c2 = st.columns(2)
    with c1:
        page_id = st.text_input("MDA ID", manifest.get("id", stem.split("-")[0] if stem.startswith("MDA") else stem))
        filename = st.text_input("Output filename", manifest.get("filename", f"{stem}.html"))
        public_title = st.text_input("Public title", manifest.get("public_title", manifest.get("title", stem)))
        seo_title = st.text_input("SEO title", manifest.get("seo_title", f"{public_title} | The Moral Decline of America"))
    with c2:
        status = st.selectbox("Status", ["draft", "audit", "production"], index=["draft", "audit", "production"].index(manifest.get("status", "audit")))
        brand = st.text_input("Brand", manifest.get("brand", "The Moral Decline of America"))
        canonical = st.text_input("Canonical path", manifest.get("canonical", f"/moral-decline/{filename}"))
        meta_description = st.text_area("Meta description", manifest.get("meta_description", "A model-based analysis page in The Moral Decline of America series."), height=92)

    st.subheader("2. Components / slots")
    s1, s2, s3 = st.columns(3)
    with s1:
        layout = st.selectbox("Layout", ["article"], index=0)
        topbar = st.selectbox("Top bar", list_names("topbars"), index=list_names("topbars").index(manifest.get("topbar", "main")) if manifest.get("topbar", "main") in list_names("topbars") else 0)
        nav = st.selectbox("Navigation", list_names("navs"), index=list_names("navs").index(manifest.get("nav", "mda")) if manifest.get("nav", "mda") in list_names("navs") else 0)
    with s2:
        hero = st.selectbox("Hero / top visual", list_names("heroes"), index=list_names("heroes").index(manifest.get("hero", "blackboard")) if manifest.get("hero", "blackboard") in list_names("heroes") else 0)
        sidebar = st.selectbox("Sidebar", list_names("sidebars"), index=list_names("sidebars").index(manifest.get("sidebar", "toc")) if manifest.get("sidebar", "toc") in list_names("sidebars") else 0)
        footer = st.selectbox("Footer", list_names("footers"), index=list_names("footers").index(manifest.get("footer", "standard")) if manifest.get("footer", "standard") in list_names("footers") else 0)
    with s3:
        audio = st.checkbox("Audio player", value=bool(manifest.get("audio", False)))
        proof_layer = st.selectbox("Audit/proof layer", ["hidden", "visible"], index=["hidden", "visible"].index(manifest.get("proof_layer", "hidden")))
        related_ring = st.selectbox("Related-work ring", ["hidden", "visible"], index=["hidden", "visible"].index(manifest.get("related_ring", "hidden")))

    st.subheader("3. Theme controls")
    t1, t2, t3 = st.columns(3)
    with t1:
        bg = st.color_picker("Background", manifest.get("theme", {}).get("bg", "#101114"))
        panel = st.color_picker("Panel", manifest.get("theme", {}).get("panel", "#181b20"))
    with t2:
        text = st.color_picker("Text", manifest.get("theme", {}).get("text", "#f1f1ee"))
        muted = st.color_picker("Muted text", manifest.get("theme", {}).get("muted", "#b9b6aa"))
    with t3:
        line = st.color_picker("Lines", manifest.get("theme", {}).get("line", "#30343b"))
        accent = st.color_picker("Accent", manifest.get("theme", {}).get("accent", "#d7b56d"))

    w1, w2 = st.columns(2)
    with w1:
        content_max = st.text_input("Content width CSS", manifest.get("theme", {}).get("content_max", "820px"))
    with w2:
        sidebar_width = st.text_input("Sidebar width CSS", manifest.get("theme", {}).get("sidebar_width", "280px"))

    st.subheader("4. Markdown content")
    edited_md = st.text_area("Article source", raw_md, height=480)

with right:
    st.subheader("Build controls")
    manifest_data = {
        "id": page_id,
        "filename": filename,
        "canonical": canonical,
        "public_title": public_title,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "status": status,
        "brand": brand,
        "layout": layout,
        "topbar": None if topbar == "hidden" else topbar,
        "hero": None if hero == "hidden" else hero,
        "nav": None if nav == "hidden" else nav,
        "sidebar": None if sidebar == "hidden" else sidebar,
        "footer": None if footer == "hidden" else footer,
        "audio": audio,
        "proof_layer": proof_layer,
        "related_ring": related_ring,
        "theme": {
            "bg": bg,
            "panel": panel,
            "text": text,
            "muted": muted,
            "line": line,
            "accent": accent,
            "content_max": content_max,
            "sidebar_width": sidebar_width,
        },
    }

    st.code(yaml.safe_dump(manifest_data, sort_keys=False, allow_unicode=True), language="yaml")

    b1, b2, b3 = st.columns(3)
    with b1:
        save_clicked = st.button("Save settings + content", type="primary")
    with b2:
        build_clicked = st.button("Build page")
    with b3:
        validate_clicked = st.button("Validate HTML")

    if save_clicked:
        source_path.write_text(edited_md, encoding="utf-8")
        save_manifest(stem, manifest_data)
        st.success("Saved Markdown and manifest.")

    output_path = OUTPUT_DIR / filename

    if build_clicked:
        source_path.write_text(edited_md, encoding="utf-8")
        save_manifest(stem, manifest_data)
        code, out = run_command([sys.executable, "scripts/build_page.py", f"content/{source_path.name}"])
        if code == 0:
            st.success(out)
        else:
            st.error(out)

    if validate_clicked:
        if not output_path.exists():
            st.warning("Build the page first.")
        else:
            code, out = run_command([sys.executable, "scripts/validate_page.py", str(output_path.relative_to(ROOT))])
            if code == 0:
                st.success(out)
            else:
                st.error(out)

    if st.button("Run full publish gate"):
        source_path.write_text(edited_md, encoding="utf-8")
        save_manifest(stem, manifest_data)
        code, out = run_command([sys.executable, "scripts/publish_gate.py"])
        st.code(out)
        if code == 0:
            st.success("Publish gate passed.")
        else:
            st.error("Publish gate failed.")

    st.subheader("Preview")
    if output_path.exists():
        preview_html = output_path.read_text(encoding="utf-8")
        st.components.v1.html(preview_html, height=780, scrolling=True)
    else:
        st.info("No built HTML yet for this page.")

    st.subheader("Output file")
    st.write(str(output_path.relative_to(ROOT)))
