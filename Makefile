# Documentation and reference for shell commands

# Launch a command with `make $cmd` (selecting one $cmd below)

install-dev:
	# Install dependencies for local development usage
	uv sync --all-groups --all-extras
	uv run prek install

export-dependencies: export-base-dependencies export-dev-dependencies export-doc-dependencies

export-base-dependencies:
	# Update requirements file for web service
	uv export --no-dev --no-hashes --no-annotate --output-file web/requirements.app.txt

export-dev-dependencies:
	# Update requirements file for development environment used in GitHub Actions
	uv export --only-group dev --no-hashes --no-annotate --output-file web/requirements.dev.txt

export-doc-dependencies:
	# Update requirements file for development environment used in GitHub Actions
	uv export --group doc --no-hashes --no-annotate --output-file web/requirements.doc.txt

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
