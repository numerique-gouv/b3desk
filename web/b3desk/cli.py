import click
from flask.cli import FlaskGroup


def create_app_wrapper():
    from b3desk import create_app

    return create_app()


class B3DeskGroup(FlaskGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = [p for p in self.params if p.name != "app"]


@click.group(cls=B3DeskGroup, create_app=create_app_wrapper)
def main():
    """B3Desk management CLI."""
