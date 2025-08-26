# Simple one-file project structure generator
# Copy this code and run: python -c "exec(open('temp_structure.py').read())"
# Or just run it directly in Python REPL

import os
from pathlib import Path


def show_tree(directory=".", prefix="", ignore_patterns=None, max_depth=5, current_depth=0):
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '.idea', '.vscode', 'node_modules', '.env', '.venv', 'venv']

    if current_depth >= max_depth:
        return

    directory = Path(directory)

    try:
        items = [item for item in directory.iterdir()
                 if not any(pattern in item.name for pattern in ignore_patterns)]
        items = sorted(items, key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        print(f"{prefix}[Permission Denied]")
        return

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")

        if item.is_dir():
            extension_prefix = "    " if is_last else "│   "
            show_tree(item, prefix + extension_prefix, ignore_patterns, max_depth, current_depth + 1)


# Run immediately
print("PROJECT STRUCTURE")
print("=" * 50)
show_tree(".", max_depth=5)  # Change "." to any path you want