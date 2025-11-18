"""Main CLI module for Glint """

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional

app = typer.Typer(
    name = "glint",
    help = "Your personal and private tech watch assistant",
    rich_markup_mode = "rich"
)
console = Console()

@app.command()
def config():
    """Open configuration interface """
    console.print(Panel.fit(
        "[bold blue]Glint Configuration[/bold blue]\n\n"
        "This will open the configuration interface\n"
        "where you can set: \n"
        "- Topics to watch\n"
        "- Notification schedule\n"
        "- Data sources\n"
        "- And more...",
        border_style = "blue"
    ))

    # TODO: Implémenter l'interface de configuration
    console.print("[yellow]Configuration interface coming soon![/yellow]")
#end config

@app.command()
def watch(
    topics:Optional[list[str]] = typer.Argument(None,help="Topics to watch"),
    interval: int = typer.Option(30,help="check interval in minutes")
):
    """Start watching tech topics"""
    if topics:
        console.print(f"[green]Watching topics:[/green] {','.join(topics)}")
        console.print(f"[green]Check interval:[/green] {interval} minutes")
    else:
        console.print("[red] Please specify topics to watch[/red]")
        console.print("[blue]Example: [/blue] glint watch python rust ai")
#end watch

@app.command()
def status():
    """Show current status and configuration"""
    console.print(Panel.fit(
        "[bold green]Glint Status[/bold green]\n\n"
        "[blue]Watching:[/blue] No topics set\n"
        "[blue]Interval:[/blue] 30 minutes\n"
        "[blue]Last check:[/blue] Never\n"
        "[blue]Storage:[/blue] Local files",
        border_style = "green"
    ))
#end status

def main():
    """Main entry point for Glint CLI"""
    app()
#end main

if __name__ == "__main__":
    main()
    
