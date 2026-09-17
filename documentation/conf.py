#!/usr/bin/env python3
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path("../web").resolve()))

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
    "sphinx_issues",
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

version = b3desk.__version__
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

# -- Options for sphinx-issues --------------------------------------------

# Lets the documentation write {issue}`42`, {pr}`58` or {user}`azmeuk`.
# CHANGELOG.md keeps plain Markdown links instead: it is also read on GitHub
# and copied into the release notes, where Sphinx roles would show up raw.
issues_github_path = "numerique-gouv/b3desk"

# {user} points at the sponsoring page by default, which is not what we mean.
issues_user_uri = "https://github.com/{user}"

# -- Options for autosectionlabel -----------------------------------------

autosectionlabel_prefix_document = True

# Every changelog entry repeats the same category titles, which cannot yield
# unique labels.
suppress_warnings = ["autosectionlabel.maintainers/changelog"]

# -- Options for autodo_pydantic_settings -------------------------------------------

autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_field_list_validators = False
