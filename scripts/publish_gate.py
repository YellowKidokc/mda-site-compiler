from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
MANIFEST_DIR = ROOT / "manifests"
OUTPUT_DIR = ROOT / "output" / "moral-decline"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT)
    return completed.returncode


def main() -> None:
    failures = 0
    for manifest_file in sorted(MANIFEST_DIR.glob("*.yml")):
        failures += run([sys.executable, "scripts/validate_page.py", str(manifest_file.relative_to(ROOT))])

    for md_file in sorted(CONTENT_DIR.glob("*.md")):
        failures += run([sys.executable, "scripts/build_page.py", str(md_file.relative_to(ROOT))])

    for html_file in sorted(OUTPUT_DIR.glob("*.html")):
        failures += run([sys.executable, "scripts/validate_page.py", str(html_file.relative_to(ROOT))])

    if failures:
        print("Publish gate failed.")
        raise SystemExit(1)
    print("Publish gate passed.")


if __name__ == "__main__":
    main()
