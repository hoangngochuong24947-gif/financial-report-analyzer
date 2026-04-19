#!/usr/bin/env python3
"""Run a lightweight Playwright smoke test against the local app."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "playwright"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Playwright smoke test.")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:5173/metrics", help="Frontend page to open.")
    parser.add_argument("--timeout-ms", type=int, default=90000, help="Wait timeout for key UI elements.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results: dict[str, object] = {
        "steps": [],
        "requests": [],
        "console_errors": [],
        "page_errors": [],
    }

    def record_step(name: str, ok: bool, detail: str) -> None:
        results["steps"].append({"step": name, "ok": ok, "detail": detail})
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {detail}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})

        request_start: dict[str, float] = {}

        def on_request(request) -> None:
            if "/api/" in request.url:
                request_start[request.url] = time.time()

        def on_response(response) -> None:
            if "/api/" not in response.url:
                return
            started_at = request_start.get(response.url)
            results["requests"].append(
                {
                    "url": response.url,
                    "status": response.status,
                    "duration_s": None if started_at is None else round(time.time() - started_at, 2),
                }
            )

        page.on("request", on_request)
        page.on(
            "console",
            lambda message: results["console_errors"].append({"type": message.type, "text": message.text})
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda exc: results["page_errors"].append(str(exc)))
        page.on("response", on_response)

        page.goto(args.frontend_url, wait_until="domcontentloaded", timeout=20000)
        record_step("open metrics page", True, f"loaded route {page.url}")

        try:
            start = time.time()
            page.wait_for_function("() => document.querySelectorAll('.stock-item').length > 0", timeout=args.timeout_ms)
            elapsed = round(time.time() - start, 2)
            stock_count = page.locator(".stock-item").count()
            first_stock = page.locator(".stock-item").first.inner_text()
            record_step("stock list loaded", True, f"{stock_count} items visible after {elapsed}s; first={first_stock!r}")
        except PlaywrightTimeoutError:
            page.screenshot(path=str(OUTPUT_DIR / "metrics-timeout.png"), full_page=True)
            record_step("stock list loaded", False, f"timed out after {args.timeout_ms}ms")
            stock_count = 0

        tab_locator = page.locator('[role="tab"]')
        tab_texts = [tab_locator.nth(index).inner_text() for index in range(tab_locator.count())]
        record_step("route tabs present", len(tab_texts) >= 3, str(tab_texts))

        if stock_count > 0:
            page.locator(".stock-item").first.click()
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUTPUT_DIR / "metrics-after-select.png"), full_page=True)
            record_step("select first stock", True, "clicked first stock item")
        else:
            record_step("select first stock", False, "skipped because no stock item became available")

        if tab_locator.count() >= 3:
            tab_locator.nth(1).click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUTPUT_DIR / "models-page.png"), full_page=True)
            record_step("navigate to models", "/models" in page.url, page.url)

            page.locator('[role="tab"]').nth(2).click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUTPUT_DIR / "insights-page.png"), full_page=True)
            record_step("navigate to insights", "/insights" in page.url, page.url)

        browser.close()

    result_path = OUTPUT_DIR / "playwright-test-results.json"
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved results to {result_path}")

    has_failure = any(not step["ok"] for step in results["steps"])
    return 1 if has_failure else 0


if __name__ == "__main__":
    sys.exit(main())
