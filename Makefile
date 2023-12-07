# Documentation and reference for shell commands

# Launch a command with `make $cmd` (selecting one $cmd below)

install-dev:
	# Install dependencies for local development usage
	poetry install --with dev --with doc; poetry shell
	pre-commit install

export-dependencies: export-base-dependencies export-dev-dependencies export-doc-dependencies

export-base-dependencies:
	# Update requirements file for web service
	poetry export --without-hashes --with task-management -o web/requirements.app.txt

export-dev-dependencies:
	# Update requirements file for development environment used in GitHub Actions
	poetry export --without-hashes --only dev -o web/requirements.dev.txt

export-doc-dependencies:
	# Update requirements file for development environment used in GitHub Actions
	poetry export --without-hashes --only doc -o web/requirements.doc.txt

translation-extract:
	# Extract messages to be translated with:
	pybabel extract --mapping-file web/translations/babel.cfg --output-file web/translations/messages.pot --keywords lazy_gettext web

translation-update:
	# Update translation catalogs with:
	pybabel update --input-file web/translations/messages.pot --output-dir web/translations

translation-compile:
	# Compile translation catalogs with:
	pybabel compile --directory web/translations

doc:
	sphinx-build documentation build/sphinx/html
