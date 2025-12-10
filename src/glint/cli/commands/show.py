import typer
import time
import threading
from rich.console import Console
app = typer.Typer()
console = Console()

@app.command()
def show(
    port: int = typer.Option(5000, help="Port to run the dashboard on"),
    no_browser: bool = typer.Option(False, help="Don't open the browser automatically")
):
    """
    Launch the Glint Web Dashboard.
    """
    # Lazy import to avoid crashing CLI if web dependencies are missing
    from glint.web.server import start_server, open_dashboard

    console.print(f"[bold green]Starting Glint Dashboard on http://127.0.0.1:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")

    if not no_browser:
        # Open browser after a short delay to ensure server is up
        threading.Timer(1.5, lambda: open_dashboard(port)).start()

    try:
        start_server(port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping Glint Dashboard...[/yellow]")
