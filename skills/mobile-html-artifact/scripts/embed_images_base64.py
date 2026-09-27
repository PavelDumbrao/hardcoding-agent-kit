#!/usr/bin/env python3
"""
Embed local HTML image sources as base64 data URIs.

Usage:
  python embed_images_base64.py index.html index_embedded.html --base-dir .
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
from pathlib import Path

IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])(?!data:|https?:|//)([^"\']+)(\2)', re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed local <img src> files as base64 data URIs.")
    parser.add_argument("input_html", type=Path, help="Source HTML file.")
    parser.add_argument("output_html", type=Path, help="Output HTML file.")
    parser.add_argument("--base-dir", type=Path, default=Path("."), help="Base directory for relative image paths.")
    return parser.parse_args()


def make_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def main() -> int:
    args = parse_args()

    if not args.input_html.exists():
        print(f"HTML file not found: {args.input_html}")
        return 1

    html = args.input_html.read_text(encoding="utf-8")
    base_dir = args.base_dir.resolve()
    embedded = 0
    missing: list[str] = []

    def replace_src(match: re.Match[str]) -> str:
        nonlocal embedded
        prefix, quote, raw_src, suffix = match.groups()
        image_path = (base_dir / raw_src).resolve()

        try:
            image_path.relative_to(base_dir)
        except ValueError:
            missing.append(raw_src)
            return match.group(0)

        if not image_path.exists() or not image_path.is_file():
            missing.append(raw_src)
            return match.group(0)

        embedded += 1
        return f"{prefix}{quote}{make_data_uri(image_path)}{suffix}"

    result = IMG_SRC_RE.sub(replace_src, html)
    args.output_html.write_text(result, encoding="utf-8")

    print(f"Embedded images: {embedded}")
    if missing:
        print("Skipped missing or unsafe paths:")
        for item in missing:
            print(f"- {item}")

    size_mb = args.output_html.stat().st_size / (1024 * 1024)
    print(f"Output: {args.output_html} | {size_mb:.2f} MB")
    return 0 if embedded > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
