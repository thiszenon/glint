""" Set your theme """

import typer
from rich.console import Console
import customtkinter as ctk
import json
from pathlib import Path

console = Console()
app = typer.Typer()

@app.command()
def set_theme(mode : str):
    """ set the theme mode (dark or light)"""
    if mode.lower() not in ["dark", "light"]:
        console.print("[red]Invalid theme mode. Use 'dark' or 'light'[/red]")
        return

    theme = mode.capitalize()
    save_theme_preference(theme)
    console.print(f"[green]Theme set to {theme} mode [/green]")
    console.print(f"[green]Restart the app to apply the theme[/green]")

#end set_theme

@app.command()
def show():
    """ show the current theme """
    theme = load_theme_preference() 
    console.print(f"[blue]Current theme: {theme}[/blue]")

def save_theme_preference(theme: str):
    """Save theme preference to config"""
    try:
        config_path = Path.home() / ".glint" / "config.json"
        
        # Load existing config
        config = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Update theme
        config["theme"] = theme
        
        # Save back
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        console.print(f"[red]Error saving theme: {e}[/red]")

#end save_theme_preference


def load_theme_preference() -> str:
    """Load theme preference from config"""
    try:
        config_path = Path.home() / ".glint" / "config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("theme", "Light")
    except:
        pass
    
    return "Light"  # Default