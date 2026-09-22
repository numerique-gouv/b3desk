"""Point out, in each changelog entry, the revision the database lands on.

The sentence cannot live in a changelog fragment: scriv merges the fragments of
a release under a single heading, so the last revision of a batch is only known
once the entry is collected.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
VERSIONS = ROOT / "web" / "migrations" / "versions"

SENTENCE = "Une fois la mise à jour terminée, `flask db current` renvoie `{head}`."
SENTENCE_START = SENTENCE.split("`")[0]

REVISION_RE = re.compile(r'^revision = "([^"]+)"', re.MULTILINE)
DOWN_REVISION_RE = re.compile(r'^down_revision = (?:"([^"]+)"|None)', re.MULTILINE)
CITATION_RE = re.compile(r"\[`([0-9a-f]+)`\]")
SECTION_RE = re.compile(r"(?ms)^### Migrations\n(.*?)(?=^### |^<a id=|\Z)")
ENTRY_RE = re.compile(r"(?m)^## ")


def read_parents():
    """Map each revision to the one it revises."""
    parents = {}
    for path in sorted(VERSIONS.glob("*.py")):
        source = path.read_text()
        revision = REVISION_RE.search(source)
        down_revision = DOWN_REVISION_RE.search(source)
        if not revision or not down_revision:
            sys.exit(f"{path.name} : revision ou down_revision introuvable")
        parents[revision.group(1)] = down_revision.group(1)
    return parents


def head_of(batch, parents):
    """Return the revision of the batch that no other revision of the batch revises."""
    unknown = [revision for revision in batch if revision not in parents]
    if unknown:
        sys.exit(f"révisions citées mais absentes de {VERSIONS} : {', '.join(unknown)}")

    revised = {parents[revision] for revision in batch}
    heads = [revision for revision in batch if revision not in revised]
    if len(heads) != 1:
        sys.exit(f"le lot {batch} a {len(heads)} têtes de chaîne au lieu d'une")
    return heads[0]


def mark_section(body, parents):
    """Set the closing sentence of a Migrations section, replacing any previous one."""
    bullets = "\n".join(
        line for line in body.splitlines() if not line.startswith(SENTENCE_START)
    ).rstrip()
    batch = CITATION_RE.findall(bullets)
    if not batch:
        return body
    return f"{bullets}\n\n{SENTENCE.format(head=head_of(batch, parents))}\n\n"


def mark_entries(text, parents, every_entry):
    starts = [match.start() for match in ENTRY_RE.finditer(text)]
    if not starts:
        return text, []

    bounds = list(zip(starts, [*starts[1:], len(text)], strict=True))
    if not every_entry:
        bounds = bounds[:1]

    marked = []
    for start, end in reversed(bounds):
        entry = text[start:end]
        new_entry = SECTION_RE.sub(
            lambda match: "### Migrations\n" + mark_section(match.group(1), parents),
            entry,
        )
        if new_entry != entry:
            marked.append(entry.splitlines()[0].removeprefix("## "))
        text = text[:start] + new_entry + text[end:]
    return text, marked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="traiter tout l'historique et pas seulement l'entrée la plus récente",
    )
    args = parser.parse_args()

    text = CHANGELOG.read_text()
    new_text, marked = mark_entries(text, read_parents(), args.all)
    if new_text == text:
        print("rien à marquer")
        return

    CHANGELOG.write_text(new_text)
    for entry in reversed(marked):
        print(f"marqué : {entry}")


if __name__ == "__main__":
    main()
