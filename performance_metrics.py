from pathlib import Path
from typing import Dict


def collect_metrics(extension_path: str) -> Dict:
    """
    Static performance metrics (file size, type distribution).
    """
    path = Path(extension_path)
    files = [p for p in path.rglob("*") if p.is_file()]
    total_size = sum(p.stat().st_size for p in files) if files else 0

    js_size = _sum_size(files, [".js", ".mjs", ".ts"])
    css_size = _sum_size(files, [".css"])
    img_size = _sum_size(files, [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"])

    largest = _largest_file(files)

    return {
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": len(files),
        "js_size_mb": round(js_size / (1024 * 1024), 2),
        "css_size_mb": round(css_size / (1024 * 1024), 2),
        "image_size_mb": round(img_size / (1024 * 1024), 2),
        "largest_file": largest.get("name"),
        "largest_file_mb": largest.get("size_mb"),
    }


def _sum_size(files, suffixes):
    return sum(p.stat().st_size for p in files if p.suffix.lower() in suffixes)


def _largest_file(files):
    if not files:
        return {"name": None, "size_mb": 0}
    largest = max(files, key=lambda p: p.stat().st_size)
    return {
        "name": largest.name,
        "size_mb": round(largest.stat().st_size / (1024 * 1024), 2),
    }
