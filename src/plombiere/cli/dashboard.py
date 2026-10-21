"""CLI entry point for the Plombiere dashboard."""

from importlib.metadata import version as _pkg_version

import click

__version__ = _pkg_version("plombiere")


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """Plombiere provenance dashboard."""


@cli.command(name="dashboard")
@click.option("--port", default=8050, type=int, help="HTTP port to listen on")
@click.option("--debug", is_flag=True, default=False, help="Enable Dash debug / hot-reload")
@click.option(
    "--db-url",
    default="sqlite+aiosqlite:///plombiere.db",
    help="SQLAlchemy async database URL",
)
def dashboard(port: int, debug: bool, db_url: str) -> None:
    """Launch the Plombiere dashboard."""
    from plombiere.app import main
    main(port=port, debug=debug, db_url=db_url)
