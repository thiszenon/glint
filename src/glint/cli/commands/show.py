import typer
import time
import typer
import time
import threading
from rich.console import Console
app = typer.Typer()
console = Console()

@app.command()
def show(port: int = 5000, no_browser: bool = False):
    """Launch the Glint Web Dashboard without blocking the terminal.
    """
    # Lazy import to avoid crashing CLI if web dependencies are missing
    from glint.web.server import start_server, open_dashboard

    console.print(f"[bold green]Starting Glint Dashboard on http://127.0.0.1:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")

    # Start Flask server in a daemon thread so the terminal stays usable
    server_thread = threading.Thread(target=start_server, kwargs={"port": port, "debug": False}, daemon=True)
    server_thread.start()

    # Open the browser after a short delay to give the server time to start
    if not no_browser:
        threading.Timer(1.5, lambda: open_dashboard(port)).start()

    # Return immediately – the terminal remains interactive
    return
