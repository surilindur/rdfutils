"""Command like tool for miscellaneous RDF processing tasks."""

from typer import Typer

from compile import module as module_compile

app = Typer()
app.add_typer(module_compile)

if __name__ == "__main__":
    app()
