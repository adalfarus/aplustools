import os
import sys

# Make your source code importable
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "aplustools"
author = "adalfarus (Cariel Becker)"
copyright = f"2025, {author}"
release = "2.0.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",         # Auto-document from docstrings
    "sphinx.ext.napoleon",        # Support for NumPy/Google style docstrings
    "sphinxcontrib.restbuilder",  # ReST output builder
]

source_suffix = ".rst"
exclude_patterns = ["_build"]

# -- Autodoc Options ---------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": "__init__",
    "show-inheritance": True,
}

# -- ReST Builder Options ----------------------------------------------------
rst_file_suffix = ".rst"
rst_link_suffix = ""
rst_line_width = 88
rst_indent = 4

# Rename 'index.rst' to 'Home.rst' and adjust wiki links
def rst_file_transform(docname):
    if docname == "index":
        docname = "Home"
    return docname + rst_file_suffix

def rst_link_transform(docname):
    if docname == "index":
        return "wiki"
    return "wiki/" + docname
