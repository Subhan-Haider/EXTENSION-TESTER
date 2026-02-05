from pathlib import Path
from typing import Dict, List, Optional


def run_runtime_tests(
    extension_path: str,
    browsers: List[str],
    test_urls: List[str],
    capture_screenshots: bool = False,
    screenshot_dir: Optional[str] = None,
    extension_name: Optional[str] = None,
) -> Dict:
    """
    Playwright-based runtime test.
    Returns per-browser console errors and basic timings.
    If Playwright is not available, returns an error payload.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return {
            "error": "Playwright not installed. Run: pip install playwright && playwright install",
            "details": str(e),
        }

    results = {}
    ext_path = Path(extension_path).resolve()
    if not ext_path.is_dir():
        return {"error": "Extension path not found"}

    with sync_playwright() as p:
        for browser in browsers:
            if browser.lower() in ("firefox",):
                results[browser] = {"skipped": "Firefox extension loading not supported in this runner"}
                continue

            if browser.lower() == "edge":
                browser_type = p.chromium
                channel = "msedge"
            else:
                browser_type = p.chromium
                channel = "chrome"

            context = browser_type.launch_persistent_context(
                user_data_dir=str(ext_path / ".runtime_profile"),
                headless=True,
                channel=channel,
                args=[
                    f"--disable-extensions-except={ext_path}",
                    f"--load-extension={ext_path}",
                ],
            )

            console_errors = []
            timings = []

            def on_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            page = context.new_page()
            page.on("console", on_console)

            for url in test_urls:
                start = page.evaluate("performance.now()")
                try:
                    page.goto(url, wait_until="load", timeout=60000)
                    end = page.evaluate("performance.now()")
                    timings.append({"url": url, "load_ms": round(end - start, 2)})
                    if capture_screenshots and screenshot_dir:
                        shot_dir = Path(screenshot_dir) / "screenshots" / _safe_name(extension_name or ext_path.name)
                        shot_dir.mkdir(parents=True, exist_ok=True)
                        file_name = f"{browser}_{_safe_name(url)}.png"
                        shot_path = shot_dir / file_name
                        page.screenshot(path=str(shot_path), full_page=True)
                except Exception as e:
                    console_errors.append(f"{url}: {str(e)}")

            results[browser] = {
                "console_errors": console_errors,
                "timings": timings,
            }
            context.close()

    return results


def _safe_name(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")[:64]
