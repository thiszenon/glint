"""Main CLI module for Glint """

import typer
from rich.console import Console
from glint.cli.commands import init, topics, fetch, status, clear, config

app = typer.Typer(
    name = "glint",
    help = "Your personal and private tech watch assistant",
    rich_markup_mode = "rich"
)
console = Console()

# Register commands directly
app.command(name="init")(init.init)
app.command(name="add")(topics.add)
app.command(name="list")(topics.list_topics)
app.command(name="fetch")(fetch.fetch)
app.command(name="status")(status.status)
app.command(name="clear")(clear.clear)

# Register command groups
app.add_typer(config.app, name="config")

def main():
    """Main entry point for Glint CLI"""
    app()

if __name__ == "__main__":
    main()