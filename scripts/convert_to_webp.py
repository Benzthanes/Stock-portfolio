#!/usr/bin/env python3
"""Convert repository images to WebP format with quality 80 and update references."""

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def convert_all_images():
    converted = 0
    failed = 0
    orig_total = 0
    webp_total = 0

    image_exts = {".png", ".jpg", ".jpeg"}

    for root, dirs, files in os.walk(ROOT):
        if ".git" in root:
            continue
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in image_exts:
                orig_size = p.stat().st_size
                out_p = p.with_suffix(".webp")
                res = subprocess.run(
                    ["cwebp", "-q", "80", str(p), "-o", str(out_p)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if res.returncode == 0 and out_p.exists() and out_p.stat().st_size > 0:
                    webp_size = out_p.stat().st_size
                    orig_total += orig_size
                    webp_total += webp_size
                    p.unlink()
                    converted += 1
                else:
                    failed += 1
                    print(f"Failed to convert: {p}")

    print(f"Converted {converted} images (Failed: {failed})")
    print(f"Original size: {orig_total / (1024*1024):.2f} MB")
    print(f"New WebP size: {webp_total / (1024*1024):.2f} MB")
    if orig_total > 0:
        saved = orig_total - webp_total
        pct = (saved / orig_total) * 100
        print(f"Space saved: {saved / (1024*1024):.2f} MB ({pct:.1f}% reduction)")

def update_references():
    ledger_path = ROOT / "data" / "ledger.json"
    if ledger_path.exists():
        content = ledger_path.read_text(encoding="utf-8")
        new_content = re.sub(r'(\.PNG|\.png|\.jpg|\.jpeg)', '.webp', content)
        ledger_path.write_text(new_content, encoding="utf-8")
        print("Updated references in data/ledger.json")

    trades_path = ROOT / "data" / "trades.json"
    if trades_path.exists():
        content = trades_path.read_text(encoding="utf-8")
        new_content = re.sub(r'(\.PNG|\.png|\.jpg|\.jpeg)', '.webp', content)
        trades_path.write_text(new_content, encoding="utf-8")
        print("Updated references in data/trades.json")

if __name__ == "__main__":
    convert_all_images()
    update_references()
