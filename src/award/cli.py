"""Console script for award."""

import typer
from rich.console import Console

from award import utils

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


@app.command()
def main():
    """Console script for award."""
    console.print("Let us start here!")
    utils.do_something_useful()


if __name__ == "__main__":
    app()
