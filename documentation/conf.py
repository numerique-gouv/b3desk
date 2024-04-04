#!/usr/bin/env python3
import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../web"))

import b3desk

# -- General configuration ------------------------------------------------


extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinxcontrib.autodoc_pydantic",
]

templates_path = ["_templates"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"
project = "b3desk"
year = datetime.datetime.now().strftime("%Y")
copyright = f"{year}, Ministère de l'Éducation Nationale"
author = "Ministère de l'Éducation Nationale"

release = b3desk.__version__
version = "%s.%s" % tuple(map(int, release.split(".")[:2]))
language = "fr"
exclude_patterns = []
pygments_style = "sphinx"
todo_include_todos = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = []


# -- Options for HTMLHelp output ------------------------------------------

htmlhelp_basename = "b3deskdoc"
html_logo = ""


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}
latex_documents = [
    (
        master_doc,
        "b3desk.tex",
        "B3Desk Documentation",
        "Ministère de l’Éducation Nationale",
        "manual",
    )
]

# -- Options for manual page output ---------------------------------------

man_pages = [(master_doc, "b3desk", "B3Desk Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "b3desk",
        "B3Desk Documentation",
        author,
        "B3Desk",
        "BBB frontend by the French Ministry of Education.",
        "Miscellaneous",
    )
]

# -- Options for autosectionlabel -----------------------------------------

autosectionlabel_prefix_document = True

# -- Options for autodo_pydantic_settings -------------------------------------------

autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_field_list_validators = False
