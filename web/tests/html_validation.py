import html5lib
from flask_webtest import TestApp
from html5lib.constants import E


class InvalidHTMLError(AssertionError):
    """Raised when a response body cannot be parsed as valid HTML."""


def is_fragment(document):
    """Whether a document is a HTML fragment, as returned by the AJAX endpoints.

    A whole page is expected to carry a doctype, or at least a ``html`` element.
    """
    head = document.lstrip()[:2048].lower()
    return not head.startswith("<!doctype") and "<html" not in head


def html_errors(document):
    """Return the html5lib parse errors of a HTML document, as readable strings."""
    parser = html5lib.HTMLParser()
    if is_fragment(document):
        parser.parseFragment(document)
    else:
        parser.parse(document)

    lines = document.splitlines()
    errors = []
    for (line, column), code, datavars in parser.errors:
        source = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        errors.append(
            f"line {line}, column {column}: {E[code] % datavars}\n    {source}"
        )
    return errors


class ValidatingTestApp(TestApp):
    """A TestApp checking that every HTML response it gets can be parsed."""

    def do_request(self, req, status=None, expect_errors=None):
        response = super().do_request(req, status=status, expect_errors=expect_errors)

        if response.content_type != "text/html" or not response.text.strip():
            return response

        errors = html_errors(response.text)
        if errors:
            details = "\n".join(f"  - {error}" for error in errors)
            raise InvalidHTMLError(
                f"Invalid HTML in the response to {req.method} {req.path}:\n{details}"
            )

        return response
