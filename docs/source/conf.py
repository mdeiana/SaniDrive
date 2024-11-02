# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SaniDrive'
copyright = '2024, Michele Deiana'
author = 'Michele Deiana'
release = '1.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath('../../src/sanidrive'))
#sys.path.insert(0, str(Path('../..', 'src').resolve()))

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc'
]

templates_path = ['_templates']
exclude_patterns = []

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = True

autodoc_default_options = {
	'members': True,
	#'special-members': True,
	'private-members': True,
	'member-order': 'bysource'
}

autoclass_content = 'class'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
