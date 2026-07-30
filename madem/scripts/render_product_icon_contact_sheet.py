#!/usr/bin/env python3
"""Render approved product icons on transparent, black, and white backgrounds."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "assets/product-icons/v2/catalog.json",
    )
    parser.add_argument(
        "--browser",
        type=Path,
        help="Optional Chrome/Chromium executable; omit to generate HTML only.",
    )
    parser.add_argument("--update-catalog", action="store_true")
    args = parser.parse_args()

    catalog_path = args.catalog.expanduser().resolve()
    root = catalog_path.parent
    review = root / "review"
    review.mkdir(parents=True, exist_ok=True)
    html_path = review / "icon-contact-sheet.html"
    png_path = review / "icon-contact-sheet.png"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    rows = []
    for asset in catalog["assets"]:
        icon = html.escape(f"../{asset['canonical_file']}", quote=True)
        label = html.escape(asset["display_name"])
        asset_id = html.escape(asset["asset_id"])
        cells = "".join(
            f'<div class="cell {background}"><img src="{icon}" '
            f'alt="{label} on {background}"></div>'
            for background in ("transparent", "black", "white")
        )
        rows.append(
            f'<div class="name"><strong>{label}</strong>'
            f'<code>{asset_id}</code></div>{cells}'
        )

    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: 960px; min-height: 1680px; background: #10151d; color: #f7f9fc; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; }}
body {{ padding: 32px; }}
h1 {{ margin: 0 0 8px; font-size: 28px; }}
p {{ margin: 0 0 24px; color: #aeb8c7; }}
.grid {{ display: grid; grid-template-columns: 210px repeat(3, 218px); gap: 12px; align-items: stretch; }}
.head {{ height: 40px; display: grid; place-items: center; color: #c9d2df; font-weight: 700; }}
.name {{ height: 132px; border: 1px solid #273444; border-radius: 14px; padding: 24px 18px; display: flex; flex-direction: column; justify-content: center; gap: 8px; background: #121a24; }}
.name strong {{ font-size: 19px; }}
.name code {{ color: #39e58c; font-size: 14px; }}
.cell {{ height: 132px; border-radius: 14px; border: 1px solid #344155; display: grid; place-items: center; overflow: hidden; }}
.cell img {{ display: block; width: 88px; height: 88px; object-fit: contain; }}
.transparent {{ background-color: #dfe4ea; background-image: linear-gradient(45deg, #b8c0ca 25%, transparent 25%), linear-gradient(-45deg, #b8c0ca 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #b8c0ca 75%), linear-gradient(-45deg, transparent 75%, #b8c0ca 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0; }}
.black {{ background: #000; }}
.white {{ background: #fff; }}
</style>
</head>
<body>
<h1>MADEM Product Icons v2</h1>
<p>project-proven · transparent / black / white review</p>
<div class="grid">
  <div></div><div class="head">透明检查</div><div class="head">黑底</div><div class="head">白底</div>
  {''.join(rows)}
</div>
</body>
</html>
"""
    html_path.write_text(document, encoding="utf-8")

    if args.browser:
        browser = args.browser.expanduser().resolve()
        if not browser.is_file():
            raise FileNotFoundError(f"browser not found: {browser}")
        subprocess.run(
            [
                str(browser),
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                "--window-size=960,1680",
                f"--screenshot={png_path}",
                html_path.as_uri(),
            ],
            check=True,
        )
        if not png_path.is_file():
            raise RuntimeError("browser did not create the contact-sheet screenshot")

    if args.update_catalog:
        catalog.setdefault("validation", {}).update(
            {
                "backgrounds": ["transparent-checkerboard", "black", "white"],
                "contact_sheet_html": "review/icon-contact-sheet.html",
                "contact_sheet_png": (
                    "review/icon-contact-sheet.png" if png_path.is_file() else None
                ),
                "contact_sheet_sha256": sha256(png_path) if png_path.is_file() else None,
                "manual_review": "pending",
            }
        )
        catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "status": "pass",
                "html": str(html_path),
                "png": str(png_path) if png_path.is_file() else None,
                "backgrounds": ["transparent-checkerboard", "black", "white"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
