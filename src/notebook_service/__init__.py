# src/notebook_service/__init__.py
from importlib.metadata import PackageNotFoundError, version

try:                               # installed wheel / pip install -e .
    __version__ = version("notebook-to-prod-template")
except PackageNotFoundError:       # editable checkout before build
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]          # optional, keeps namespace clean
