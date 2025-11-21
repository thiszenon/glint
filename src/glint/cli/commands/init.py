import typer
from rich.console import Console
from pathlib import Path
import json
from glint.core.database import create_db_and_tables

console = Console()
app = typer.Typer()

@app.command()
def init():
    """
    Initialize the Glint environment.
    Creates the .glint directory, config file, and database.
    """
    # Define the glint directory path (user's home directory)
    glint_dir = Path.home() / ".glint"
    
    # Define paths for config
    config_path = glint_dir / "config.json"

    try:
        # Create the directory if it doesn't exist
        if not glint_dir.exists():
            glint_dir.mkdir(parents=True)
            console.print(f"[green]Created Glint directory at {glint_dir}[/green]")
        else:
            console.print(f"[yellow]Glint directory already exists at {glint_dir}[/yellow]")

        # Create default config if it doesn't exist
        if not config_path.exists():
            # TODO: Changer la configuration par defaut
            default_config = {
                "interval": 30,
                "sources": ["github", "hackernews"]
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            console.print(f"[green]Created default config at {config_path}[/green]")
        
        # Initialize Database
        console.print("[blue]Initializing database...[/blue]")
        create_db_and_tables()
        console.print("[green]Database initialized successfully![/green]")

        console.print("[bold green]Glint initialized successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error initializing Glint: {e}[/bold red]")
