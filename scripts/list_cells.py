import sys
import nbformat

def list_cells(path):
    nb = nbformat.read(path, as_version=4)
    for idx, cell in enumerate(nb.cells):
        preview = cell.source.strip().splitlines()[0] if cell.source else ""
        print(f"{idx:3d}: {cell.cell_type:<5} {preview[:60]!r}")

if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Usage: python list_cells.py <notebook-path>")
        sys.exit(1)
    list_cells(sys.argv[1])
