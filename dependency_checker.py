import json
import re
from pathlib import Path
from typing import Dict, List


class DependencyChecker:
    """Detect bundled libraries and outdated versions."""

    KNOWN_VULNERABLE = {
        "jquery": [("1.", "Upgrade to >= 3.5.0"), ("2.", "Upgrade to >= 3.5.0"), ("3.0", "Upgrade to >= 3.5.0"), ("3.1", "Upgrade to >= 3.5.0"), ("3.2", "Upgrade to >= 3.5.0"), ("3.3", "Upgrade to >= 3.5.0"), ("3.4", "Upgrade to >= 3.5.0")],
        "lodash": [("4.17.20", "Upgrade to >= 4.17.21"), ("4.17.19", "Upgrade to >= 4.17.21")],
    }

    LIB_PATTERNS = [
        (r"jquery[-\.](\d+\.\d+\.\d+)", "jquery"),
        (r"lodash[-\.](\d+\.\d+\.\d+)", "lodash"),
        (r"moment[-\.](\d+\.\d+\.\d+)", "moment"),
    ]

    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)

    def analyze(self) -> Dict:
        warnings = []
        detected = []

        pkg_json = self.extension_path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                detected.extend(self._check_versions(deps))
                detected.extend(self._check_versions(dev_deps))
            except json.JSONDecodeError:
                warnings.append("package.json is invalid JSON")

        for js_file in self.extension_path.rglob("*.js"):
            name = js_file.name.lower()
            for pattern, lib in self.LIB_PATTERNS:
                match = re.search(pattern, name)
                if match:
                    version = match.group(1)
                    detected.append(f"{lib} {version} (bundled file: {js_file.relative_to(self.extension_path)})")
                    warnings.extend(self._check_lib_version(lib, version))

        return {
            "detected": sorted(set(detected)),
            "warnings": sorted(set(warnings)),
        }

    def _check_versions(self, deps: Dict) -> List[str]:
        warnings = []
        for lib, version in deps.items():
            if lib in self.KNOWN_VULNERABLE:
                for prefix, recommendation in self.KNOWN_VULNERABLE[lib]:
                    if version.startswith(prefix):
                        warnings.append(f"{lib} {version} may be vulnerable. {recommendation}")
        return warnings

    def _check_lib_version(self, lib: str, version: str) -> List[str]:
        warnings = []
        if lib in self.KNOWN_VULNERABLE:
            for prefix, recommendation in self.KNOWN_VULNERABLE[lib]:
                if version.startswith(prefix):
                    warnings.append(f"{lib} {version} may be vulnerable. {recommendation}")
        return warnings
