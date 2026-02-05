from pathlib import Path
from typing import Dict, List, Tuple


class ExtensionSizeAnalyzer:
    """Analyze extension size and large assets."""

    DEFAULT_WARN_MB = 25
    DEFAULT_FAIL_MB = 50

    def __init__(self, extension_path: str, warn_mb: int = None, fail_mb: int = None):
        self.extension_path = Path(extension_path)
        self.warn_mb = warn_mb if warn_mb is not None else self.DEFAULT_WARN_MB
        self.fail_mb = fail_mb if fail_mb is not None else self.DEFAULT_FAIL_MB

    def analyze(self) -> Dict:
        total_bytes = 0
        by_type = {}
        largest_files: List[Tuple[str, int]] = []

        for file_path in self.extension_path.rglob("*"):
            if not file_path.is_file():
                continue
            size = file_path.stat().st_size
            total_bytes += size

            ext = file_path.suffix.lower() or "<no_ext>"
            by_type[ext] = by_type.get(ext, 0) + size
            largest_files.append((str(file_path.relative_to(self.extension_path)), size))

        largest_files.sort(key=lambda x: x[1], reverse=True)
        largest_files = largest_files[:10]

        total_mb = total_bytes / (1024 * 1024)
        warnings = []
        errors = []

        if total_mb >= self.fail_mb:
            errors.append(f"Extension size is {total_mb:.2f} MB (exceeds {self.fail_mb} MB threshold)")
        elif total_mb >= self.warn_mb:
            warnings.append(f"Extension size is {total_mb:.2f} MB (exceeds {self.warn_mb} MB threshold)")

        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_mb, 2),
            "by_type": {k: round(v / (1024 * 1024), 2) for k, v in by_type.items()},
            "largest_files": [{"file": f, "mb": round(s / (1024 * 1024), 2)} for f, s in largest_files],
            "warnings": warnings,
            "errors": errors,
        }
