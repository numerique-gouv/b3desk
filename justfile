install-dev:
    uv sync --all-groups --all-extras
    uv run prek install

translation-extract:
    uv run pybabel extract --omit-header --mapping-file pyproject.toml --output-file web/translations/messages.pot --keywords lazy_gettext web

translation-update:
    uv run pybabel update --input-file web/translations/messages.pot --output-dir web/translations

translation-compile:
    uv run pybabel compile --directory web/translations

doc:
    uv run sphinx-build documentation build/sphinx/html

test:
    uv run pytest -nauto

diff-cover:
    git fetch https://github.com/numerique-gouv/b3desk.git main
    uv run pytest -nauto --cov --cov-report=xml
    uv run diff-cover coverage.xml --compare-branch=FETCH_HEAD --fail-under=100
