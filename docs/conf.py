# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path

# Add source code to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

project = "metabintools"
copyright = "2026, Genome Research Ltd"
author = "Jim Downie"
release = "0.4.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Napoleon extension settings (for Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# autodoc settings
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# HTML output settings
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
}

# Intersphinx for cross-referencing
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

# Source file encoding
source_encoding = "utf-8"

# Highlight options
highlight_language = "python"

# Master document
master_doc = "index"

# Language
language = "en"

# Pygments style
pygments_style = "sphinx"


# Suppress warnings
suppress_warnings = [
    "app.add_autodocumenter",
    "misc.highlighting_failure",
    "intersphinx.external",
]
