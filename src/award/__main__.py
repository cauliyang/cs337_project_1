from typer import Typer

from .cli import extract, preprocess

app = Typer(context_settings={"help_option_names": ["-h", "--help"]})

app.command()(preprocess.main)
app.command()(extract.main)


if __name__ == "__main__":
    app()
