from pathlib import Path
from typing import Dict, List


COMMON_HTML = [
    "popup.html",
    "options.html",
    "index.html",
    "share.html",
    "settings.html",
]


def capture_static_screenshots(extension_path: str, out_dir: str, extension_name: str) -> Dict:
    """
    Capture screenshots of common local HTML files using Playwright.
    Returns {"screenshots": [relative paths], "error": "..."}.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return {"screenshots": [], "error": f"Playwright not installed: {e}"}

    path = Path(extension_path)
    if not path.is_dir():
        return {"screenshots": [], "error": "Extension path not found"}

    html_files = []
    for name in COMMON_HTML:
        p = path / name
        if p.exists():
            html_files.append(p)

    # Limit to avoid huge sets
    if not html_files:
        # fallback: any html in root
        html_files = list(path.glob("*.html"))[:5]
    else:
        html_files = html_files[:5]

    if not html_files:
        return {"screenshots": [], "error": "No HTML files found for static screenshots"}

    out_root = Path(out_dir) / "screenshots" / _safe_name(extension_name)
    out_root.mkdir(parents=True, exist_ok=True)

    rel_paths: List[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        for html in html_files:
            file_uri = html.resolve().as_uri()
            try:
                page.goto(file_uri, wait_until="load", timeout=30000)
                shot_path = out_root / f"{html.stem}.png"
                page.screenshot(path=str(shot_path), full_page=True)
                rel_paths.append(str(Path("screenshots") / _safe_name(extension_name) / shot_path.name))
            except Exception:
                continue
        browser.close()

    return {"screenshots": rel_paths, "error": None}


def _safe_name(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")[:64]
