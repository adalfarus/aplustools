import os
import sys

# Make your source code importable
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'aplustools'
author = 'adalfarus (Cariel Becker)'
copyright = '2025, ' + author
release = '2.0.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'myst_parser',              # To support Markdown parsing
    'sphinx.ext.autodoc',       # Auto-document from docstrings
    'sphinx.ext.napoleon',      # Support for NumPy/Google style docstrings
]

# Treat both .md and .rst files as sources
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

exclude_patterns = ['_build']

# -- Autodoc Options ---------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'private-members': False,
    'special-members': '__init__',
    'show-inheritance': True,
}
