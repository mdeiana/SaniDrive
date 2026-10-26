# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SaniDrive'
copyright = '2026, Michele Deiana'
author = 'Michele Deiana'
release = '1.5.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath('../../src'))
#sys.path.insert(0, str(Path('../..', 'src').resolve()))

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
#    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = []

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True

autodoc_default_options = {
	'members': True,
	#'special-members': True,
	'private-members': True,
	'member-order': 'bysource',
    "typehints" : "description", # : "signature"
}

autoclass_content = 'class'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
