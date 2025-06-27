# setup.py
from setuptools import setup, find_packages

setup(
    name="notebook_to_prod_template",
    version="0.1.0",
    # look for packages under src/
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pandas",
        "nbclient",
        "nbformat",
        "ibm-watson",
        "ibm-cloud-sdk-core",
        # …and any other deps your requirements.txt lists
    ],
    python_requires=">=3.8",
)
