# Documentation and reference for shell commands

# Launch a command with `make $cmd` (selecting one $cmd below)

install-dev:
	# Install dependencies for local development usage
	uv sync --all-groups --all-extras
	uv run prek install

translation-extract:
	# Extract messages to be translated with:
	uv run pybabel extract --mapping-file web/translations/babel.cfg --output-file web/translations/messages.pot --keywords lazy_gettext web

translation-update:
	# Update translation catalogs with:
	uv run pybabel update --input-file web/translations/messages.pot --output-dir web/translations

translation-compile:
	# Compile translation catalogs with:
	uv run pybabel compile --directory web/translations

doc:
	uv run sphinx-build documentation build/sphinx/html
