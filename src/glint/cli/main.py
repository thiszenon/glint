"""Main CLI module for Glint"""

import typer
import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from sqlmodel import Session, select, func
from glint.core.database import get_engine, create_db_and_tables
from glint.core.models import Topic
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

def run_onboarding():
    """Run the first-time onboarding wizard."""
    console.print(Panel.fit(
        "[bold blue]Welcome to Glint! ⚡[/bold blue]\n\n"
        "Your private, local tech watch assistant.\n"
        "Let's get you set up in 30 seconds.",
        border_style="blue"
    ))
    
    # 1. Ask for topics
    topics_str = questionary.text(
        "What topics are you interested in? (comma separated)\n"
        "e.g. Python, AI, React, Rust"
    ).ask()
    
    if not topics_str:
        console.print("[yellow]No topics entered. You can add them later with 'glint add'.[/yellow]")
        return

    # 2. Add topics
    topic_names = [t.strip() for t in topics_str.split(',') if t.strip()]
    engine = get_engine()
    with Session(engine) as session:
        for name in topic_names:
            if not session.exec(select(Topic).where(Topic.name == name)).first():
                session.add(Topic(name=name))
                console.print(f"[green]+ Added topic: {name}[/green]")
        session.commit()
    
    # 3. Initial Fetch
    if questionary.confirm("Ready to fetch trends now?").ask():
        fetch.fetch()
        
    # 4. Show Dashboard
    if questionary.confirm("Open the dashboard?").ask():
        show.show(port=5000, no_browser=False)

def main():
    """Main entry point for Glint CLI"""
    # Ensure DB exists
    create_db_and_tables()
    
    # Check if first run (no topics) AND no arguments provided
    if len(sys.argv) == 1:
        try:
            engine = get_engine()
            with Session(engine) as session:
                count = session.exec(select(func.count(Topic.id))).one()
            
            if count == 0:
                run_onboarding()
                return # Exit after onboarding
        except Exception as e:
            # If DB error, just let Typer handle it or fail gracefully
            pass

    app()

if __name__ == "__main__":
    main()