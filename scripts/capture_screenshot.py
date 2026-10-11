#!/usr/bin/env python3
"""Capture the running Streamlit app after executing a real demo query."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/screenshots/retailmind-demo.png"),
    )
    return parser.parse_args()


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "请先执行：pip install playwright && playwright install chromium"
        ) from exc

    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto(args.url, wait_until="networkidle")
        page.get_by_role("button", name="运行分析 →").click()
        page.get_by_text("分析完成", exact=True).wait_for(timeout=30_000)
        page.get_by_text("月度销售趋势", exact=True).wait_for(timeout=30_000)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()
    print(f"Saved real runtime screenshot to {args.output.resolve()}")


if __name__ == "__main__":
    main()

