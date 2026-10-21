"""Entry point for running the Plombiere dashboard directly."""

from plombiere.backend import BackendProvider, BackendSettings
from plombiere.dashboard import create_app


def main(
    port: int = 8050,
    debug: bool = True,
    db_url: str = "sqlite+aiosqlite:///plombiere.db",
) -> None:
    settings = BackendSettings(db_url=db_url)
    provider = BackendProvider.get()
    provider.configure(settings)
    provider.initialize()

    app = create_app(debug=debug)
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    main()
