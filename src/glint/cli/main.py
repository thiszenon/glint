"""Main CLI module for Glint"""

import typer
import sys
from rich.console import Console
from glint.core.database import create_db_and_tables
from glint.cli.commands import init, topics, fetch, status, clear, config, show, daemon, analyze, cache
from glint.core.logger import setup_logging

# Setup logging
setup_logging()

app = typer.Typer(
    name="glint",
    help="Your personal and private tech watch assistant",
    rich_markup_mode="rich"
)
console = Console()

# Register commands directly
app.command(name="init")(init.init)
app.command(name="add")(topics.add)
app.command(name="list")(topics.list_topics)
app.command(name="fetch")(fetch.fetch)
app.command(name="status")(status.status)
app.command(name="clear")(clear.clear)
app.command(name="show")(show.show)
app.command(name="daemon")(daemon.start)

# Register command groups
app.add_typer(config.app, name="config")
app.add_typer(analyze.app, name="analyze")
app.add_typer(cache.app, name="cache")

def main():
    """Main entry point for Glint CLI"""
    # Ensure DB exists
    create_db_and_tables()
    
    # If no arguments provided (double-click), launch the web UI
    if len(sys.argv) == 1:
        from glint.web.server import start_server, open_dashboard
        import threading
        
        console.print("[bold green]Launching Glint...[/bold green]")
        console.print("[dim]Close this window to stop the server.[/dim]")
        
        # Open browser after short delay
        threading.Timer(1.5, lambda: open_dashboard(5000)).start()
        
        # Start server (blocks until Ctrl+C)
        start_server(port=5000)
        return
    
    # Otherwise run CLI commands
    app()

if __name__ == "__main__":
    main()