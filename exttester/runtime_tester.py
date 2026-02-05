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

    manifest = _load_manifest(ext_path / "manifest.json")

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

            ui_results = _run_ui_tests(page, browser, manifest, ext_path, screenshot_dir, extension_name)
            lifecycle = _run_lifecycle_tests(page, browser, ext_path.name)

            results[browser] = {
                "console_errors": console_errors,
                "timings": timings,
                "ui_tests": ui_results,
                "lifecycle": lifecycle,
            }
            context.close()

    return results


def _safe_name(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")[:64]


def _load_manifest(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _run_ui_tests(page, browser: str, manifest: Dict, ext_path: Path, screenshot_dir: Optional[str], extension_name: Optional[str]) -> Dict:
    """
    Best-effort UI tests: open options page / popup if available.
    """
    results = {"popup": "not tested", "options": "not tested", "errors": []}
    if browser.lower() in ("firefox",):
        results["popup"] = "skipped"
        results["options"] = "skipped"
        return results

    ext_id = _find_extension_id(page, ext_path.name)
    if not ext_id:
        results["errors"].append("Could not resolve extension ID from chrome://extensions")
        return results

    popup_path = None
    action = manifest.get("action") or manifest.get("browser_action") or {}
    if isinstance(action, dict):
        popup_path = action.get("default_popup")

    options_path = manifest.get("options_page")
    if not options_path and isinstance(manifest.get("options_ui"), dict):
        options_path = manifest.get("options_ui", {}).get("page")

    if popup_path:
        url = f"chrome-extension://{ext_id}/{popup_path}"
        try:
            page.goto(url, wait_until="load", timeout=30000)
            results["popup"] = "pass"
            _maybe_shot(page, screenshot_dir, extension_name, f"{browser}_popup")
        except Exception as e:
            results["popup"] = "fail"
            results["errors"].append(f"Popup load failed: {e}")
    else:
        results["popup"] = "not configured"

    if options_path:
        url = f"chrome-extension://{ext_id}/{options_path}"
        try:
            page.goto(url, wait_until="load", timeout=30000)
            results["options"] = "pass"
            _maybe_shot(page, screenshot_dir, extension_name, f"{browser}_options")
        except Exception as e:
            results["options"] = "fail"
            results["errors"].append(f"Options load failed: {e}")
    else:
        results["options"] = "not configured"

    return results


def _run_lifecycle_tests(page, browser: str, ext_name: str) -> Dict:
    """
    Best-effort lifecycle actions: open extensions page, try reload/disable/enable.
    """
    results = {"reload": "not tested", "disable_enable": "not tested", "errors": []}
    if browser.lower() in ("firefox",):
        results["reload"] = "skipped"
        results["disable_enable"] = "skipped"
        return results

    try:
        page.goto("chrome://extensions/", wait_until="load", timeout=30000)
        page.wait_for_timeout(1000)
        script = """
        () => {
            const manager = document.querySelector('extensions-manager');
            if (!manager || !manager.shadowRoot) return {error: 'manager not found'};
            const list = manager.shadowRoot.querySelector('extensions-item-list');
            if (!list || !list.shadowRoot) return {error: 'item list not found'};
            const items = Array.from(list.shadowRoot.querySelectorAll('extensions-item'));
            const item = items.find(i => {
                const name = i.shadowRoot?.querySelector('#name')?.innerText?.trim();
                return name && name.toLowerCase() === '%NAME%';
            });
            if (!item) return {error: 'extension not found'};
            const reloadBtn = item.shadowRoot.querySelector('cr-button#reloadButton');
            if (reloadBtn) reloadBtn.click();
            const toggle = item.shadowRoot.querySelector('cr-toggle#enableToggle');
            if (toggle) {
                toggle.click();
                toggle.click();
            }
            return {ok: true};
        }
        """.replace("%NAME%", ext_name.lower())
        result = page.evaluate(script)
        if result.get("error"):
            results["errors"].append(result["error"])
        else:
            results["reload"] = "pass"
            results["disable_enable"] = "pass"
    except Exception as e:
        results["errors"].append(str(e))
    return results


def _find_extension_id(page, ext_name: str) -> Optional[str]:
    try:
        page.goto("chrome://extensions/", wait_until="load", timeout=30000)
        page.wait_for_timeout(1000)
        script = """
        () => {
            const manager = document.querySelector('extensions-manager');
            if (!manager || !manager.shadowRoot) return null;
            const list = manager.shadowRoot.querySelector('extensions-item-list');
            if (!list || !list.shadowRoot) return null;
            const items = Array.from(list.shadowRoot.querySelectorAll('extensions-item'));
            const item = items.find(i => {
                const name = i.shadowRoot?.querySelector('#name')?.innerText?.trim();
                return name && name.toLowerCase() === '%NAME%';
            });
            if (!item) return null;
            const id = item.getAttribute('id');
            return id || item.shadowRoot?.querySelector('#extension-id')?.innerText?.trim() || null;
        }
        """.replace("%NAME%", ext_name.lower())
        return page.evaluate(script)
    except Exception:
        return None


def _maybe_shot(page, screenshot_dir: Optional[str], extension_name: Optional[str], name: str):
    if not screenshot_dir:
        return
    shot_dir = Path(screenshot_dir) / "screenshots" / _safe_name(extension_name or "extension")
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_path = shot_dir / f"{_safe_name(name)}.png"
    try:
        page.screenshot(path=str(shot_path), full_page=True)
    except Exception:
        pass
