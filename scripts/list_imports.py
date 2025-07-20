#!/usr/bin/env python3
import ast
import nbformat
from pathlib import Path

def find_files(root: Path):
    # Walk every file in the tree
    for path in root.rglob("*"):
        if path.suffix not in {".py", ".ipynb"}:
            continue
        # Skip venvs, caches, hidden dirs
        if any(part in ("venv", ".venv", "__pycache__") or part.startswith(".")
               for part in path.parts):
            continue
        yield path

def collect_imports_from_code(code: str):
    mods = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    return mods

def collect_imports(path: Path):
    if path.suffix == ".py":
        text = path.read_text(encoding="utf-8")
        return collect_imports_from_code(text)
    else:  # .ipynb
        nb = nbformat.read(str(path), as_version=4)
        mods = set()
        for cell in nb.cells:
            if cell.cell_type == "code" and cell.source:
                mods |= collect_imports_from_code(cell.source)
        return mods

def main():
    root = Path.cwd()      # scan the whole project tree
    all_imports = {}
    for path in find_files(root):
        mods = collect_imports(path)
        if mods:
            all_imports[path.relative_to(root)] = sorted(mods)

    # Pretty‑print
    maxlen = max((len(str(p)) for p in all_imports), default=0)
    header = f"{'File':<{maxlen}}   Imported modules"
    print(header)
    print("-" * len(header))
    for path, mods in sorted(all_imports.items()):
        print(f"{str(path):<{maxlen}}   {', '.join(mods)}")

if __name__ == "__main__":
    main()
