from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "manifest_schema.yml"

BAD_ENCODING_PATTERNS = ["Ã¢", "Ã¯Â¿Â½", "Ãƒ", "ï¿½", "Â©", "?? Theophysics"]
OLD_LABEL_PATTERNS = [r"Part\s+\d+\s+of\s+\d+", r"\b03/10\b", r"\b09/10\b"]
FORBIDDEN_PUBLIC_BRAND = "Moral Decay of America"


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        return {}
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8")) or {}


def validate_manifest(path: Path) -> list[str]:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    schema = load_schema()
    errors: list[str] = []

    for key in schema.get("required", []):
        if manifest.get(key) in (None, ""):
            errors.append(f"Manifest missing required field: {key}")

    for key, allowed_values in schema.get("allowed", {}).items():
        value = manifest.get(key)
        if value not in (None, "") and value not in allowed_values:
            errors.append(f"Manifest field {key} has invalid value: {value}")

    filename = manifest.get("filename", "")
    canonical = manifest.get("canonical", "")
    filename_pattern = schema.get("filename_pattern")
    if filename_pattern and filename and not re.match(filename_pattern, filename):
        errors.append(f"Manifest filename does not match pattern: {filename}")

    canonical_prefix = schema.get("canonical_prefix", "")
    if canonical and not canonical.startswith(canonical_prefix):
        errors.append(f"Manifest canonical must start with {canonical_prefix}: {canonical}")
    if filename and canonical and canonical != f"{canonical_prefix}{filename}":
        errors.append(f"Manifest canonical must equal {canonical_prefix}{filename}: {canonical}")

    min_description = int(schema.get("min_meta_description_length", 50))
    description = str(manifest.get("meta_description", "")).strip()
    if len(description) < min_description:
        errors.append(f"Manifest meta_description is shorter than {min_description} characters.")

    haystack = "\n".join(str(value) for value in manifest.values())
    if FORBIDDEN_PUBLIC_BRAND in haystack:
        errors.append("Manifest contains old 'Moral Decay of America' branding.")

    return errors


def validate_html(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    errors: list[str] = []

    canonical = soup.find("link", rel="canonical")
    if not canonical or not canonical.get("href"):
        errors.append("Missing canonical URL.")
    elif not canonical["href"].endswith(path.name):
        errors.append(f"Canonical URL does not match filename: {canonical['href']} vs {path.name}")

    title = soup.find("title")
    if not title or not title.text.strip():
        errors.append("Missing SEO title.")

    desc = soup.find("meta", attrs={"name": "description"})
    if not desc or not desc.get("content") or len(desc.get("content", "").strip()) < 50:
        errors.append("Missing or weak meta description.")

    for bad in BAD_ENCODING_PATTERNS:
        if bad in html:
            errors.append(f"Possible encoding corruption found: {bad}")

    for pattern in OLD_LABEL_PATTERNS:
        if re.search(pattern, html, flags=re.IGNORECASE):
            errors.append(f"Old draft numbering label found: {pattern}")

    if FORBIDDEN_PUBLIC_BRAND in html:
        errors.append("Old 'Moral Decay of America' branding found.")

    topbars = soup.select("header.topbar")
    if len(topbars) > 1:
        errors.append(f"Duplicate topbars found: {len(topbars)}")

    audio_css = soup.find_all("link", href="/assets/css/audio-player.css")
    audio_js = soup.find_all("script", src="/assets/js/audio-player.js")
    if len(audio_css) > 1:
        errors.append("Duplicate audio CSS found.")
    if len(audio_js) > 1:
        errors.append("Duplicate audio JS found.")

    if "No claim from this article survived" in html:
        errors.append("Dangerous proof wording found: 'No claim from this article survived'.")

    if "Connections should be populated before production" in html:
        errors.append("Placeholder related-work ring is visible.")

    body = soup.find("body")
    if body and body.get("data-brand") != "The Moral Decline of America":
        errors.append(f"Unexpected public brand: {body.get('data-brand')}")
    if body and body.get("data-status") == "production" and errors:
        errors.append("Page is marked production while validation errors exist.")

    return errors


def validate(path: Path) -> list[str]:
    if path.suffix.lower() in {".yml", ".yaml"}:
        return validate_manifest(path)
    return validate_html(path)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/validate_page.py PAGE.html|PAGE.yml")
    path = Path(sys.argv[1])
    errors = validate(path)
    if errors:
        print(f"FAIL: {path}")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"PASS: {path}")


if __name__ == "__main__":
    main()
