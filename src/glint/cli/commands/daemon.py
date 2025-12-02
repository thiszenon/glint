import typer
import time
import signal
import sys
from rich.console import Console
from glint.core.notifier import Notifier

console = Console()
app = typer.Typer()

@app.command()
def start():
    """
    Start the Glint notification daemon in the foreground.
    This process will run continuously, checking for new trends and sending notifications.
    """
    console.print("[bold green]Starting Glint Daemon...[/bold green]")
    console.print("Press Ctrl+C to stop.")

    # Initialize Notifier
    # Default interval is 300s (5 mins), but can be passed in init
    # We'll stick to default or maybe make it configurable later
    notifier = Notifier()
    notifier.start()

    def signal_handler(sig, frame):
        console.print("\n[yellow]Stopping Glint Daemon...[/yellow]")
        notifier.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # This catch is redundant with signal handler but good for safety
        signal_handler(None, None)
