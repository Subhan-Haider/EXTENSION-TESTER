import os
from pathlib import Path
from typing import List


def find_extensions(root_folder: str) -> List[str]:
    """
    Find extension folders under root_folder.
    A folder is considered an extension if it contains manifest.json.
    """
    extensions = []
    root = Path(root_folder)
    if not root.is_dir():
        return extensions

    for current_root, dirs, files in os.walk(root_folder):
        if "manifest.json" in files:
            extensions.append(current_root)
            # Do not descend into subfolders of an extension
            dirs[:] = []

    return sorted(extensions)
