#!/usr/bin/env python3
"""
Optimize images to WebP before embedding them into autonomous HTML.

Usage:
  python optimize_images.py assets_raw assets_optimized --max-width 1400 --quality 78
"""

from __future__ import annotations

import argparse
from pathlib import Path

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize images into WebP files.")
    parser.add_argument("input_dir", type=Path, help="Directory with source images.")
    parser.add_argument("output_dir", type=Path, help="Directory for optimized WebP files.")
    parser.add_argument("--max-width", type=int, default=1400, help="Maximum output width in px.")
    parser.add_argument("--quality", type=int, default=78, help="WebP quality, usually 68-82.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("Pillow is required. Install it with: python -m pip install pillow")
        return 1

    if not args.input_dir.exists() or not args.input_dir.is_dir():
        print(f"Input directory not found: {args.input_dir}")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    for path in sorted(args.input_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS or not path.is_file():
            continue

        with Image.open(path) as source:
            image = source.convert("RGB")
            if image.width > args.max_width:
                ratio = args.max_width / image.width
                image = image.resize((args.max_width, round(image.height * ratio)), Image.LANCZOS)

            output_path = args.output_dir / f"{path.stem}.webp"
            image.save(output_path, "WEBP", quality=args.quality, method=6)
            size_kb = output_path.stat().st_size / 1024
            print(f"Saved {output_path} | {size_kb:.1f} KB")
            processed += 1

    if processed == 0:
        print("No supported images found.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
