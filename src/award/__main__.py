from typer import Typer

from .cli import preprocess

app = Typer(context_settings={"help_option_names": ["-h", "--help"]})

app.command()(preprocess.main)


if __name__ == "__main__":
    app()

