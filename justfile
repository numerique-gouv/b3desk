# Show the available recipes when just is invoked without arguments
[private]
default:
    @just --list

# Install the development dependencies and the git pre-commit hooks
[group('dev')]
install-dev:
    uv sync --all-groups --all-extras
    uv run prek install

# Build the HTML documentation with sphinx
[group('dev')]
doc:
    uv run sphinx-build documentation build/sphinx/html

# Refresh the translation catalogs from the code, end to end
[group('translation')]
translation: translation-extract translation-update translation-compile

# Collect the translatable strings from the code and templates into the .pot catalog
[group('translation')]
translation-extract:
    uv run pybabel extract --omit-header --mapping-file pyproject.toml --output-file web/translations/messages.pot --keywords lazy_gettext web

# Merge the .pot catalog into the per-language .po files
[group('translation')]
translation-update:
    uv run pybabel update --input-file web/translations/messages.pot --output-dir web/translations --no-fuzzy-matching

# Build the binary .mo catalogs actually read at runtime
[group('translation')]
translation-compile:
    uv run pybabel compile --directory web/translations

# Run the test suite, spread over all the available CPUs
[group('test')]
test:
    uv run pytest -nauto

# Check that the changes against the upstream main branch are fully covered by tests
[group('test')]
diff-cover:
    git fetch https://github.com/numerique-gouv/b3desk.git main
    uv run pytest -nauto --cov --cov-report=xml
    uv run diff-cover coverage.xml --compare-branch=FETCH_HEAD --fail-under=100
