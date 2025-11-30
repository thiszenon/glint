import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Topic, UserConfig
from datetime import datetime

console = Console()
app = typer.Typer()
topics_app = typer.Typer()
schedule_app = typer.Typer()

app.add_typer(topics_app, name="topics", help="Manage watched topics")
app.add_typer(schedule_app, name="schedule", help="Manage notification schedule")

# Secrets Management
secrets_app = typer.Typer(help="Manage API keys and secrets")
app.add_typer(secrets_app, name="secrets")

from glint.core.config import config_manager

@secrets_app.command("set")
def set_secret(key: str, value: str):
    """Set an API key (e.g., producthunt, devto)."""
    config_manager.set_secret(key, value)
    console.print(f"[green]Secret '{key}' saved successfully.[/green]")

@secrets_app.command("show")
def show_secrets():
    """Show configured secrets (masked)."""
    secrets = config_manager.get_all_secrets()
    if not secrets:
        console.print("[yellow]No secrets configured.[/yellow]")
        return

    table = Table(title="API Keys")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    
    for key, value in secrets.items():
        masked = value[:4] + "*" * (len(value)-4) if len(value) > 4 else "*" * len(value)
        table.add_row(key, masked)
        
    console.print(table)

@topics_app.command("list")
def list_topics():
    """List all watched topics and their status."""
    engine = get_engine()
    with Session(engine) as session:
        topics = session.exec(select(Topic)).all()
        
        if not topics:
            console.print("[yellow]No topics found.[/yellow]")
            return

        table = Table(title="Watched Topics")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        
        for topic in topics:
            status = "[green]Active[/green]" if topic.is_active else "[red]Inactive[/red]"
            table.add_row(str(topic.id), topic.name, status)
            
        console.print(table)

@topics_app.command("toggle")
def toggle_topic(name: str):
    """Toggle a topic between Active and Inactive."""
    engine = get_engine()
    with Session(engine) as session:
        topic = session.exec(select(Topic).where(Topic.name == name)).first()
        if not topic:
            console.print(f"[red]Topic '{name}' not found.[/red]")
            return
            
        topic.is_active = not topic.is_active
        session.add(topic)
        session.commit()
        session.refresh(topic)
        
        status = "Active" if topic.is_active else "Inactive"
        color = "green" if topic.is_active else "red"
        console.print(f"Topic '{name}' is now [{color}]{status}[/{color}].")

@topics_app.command("delete")
def delete_topic(name: str):
    """Delete a topic."""
    engine = get_engine()
    with Session(engine) as session:
        topic = session.exec(select(Topic).where(Topic.name == name)).first()
        if not topic:
            console.print(f"[red]Topic '{name}' not found.[/red]")
            return
            
        session.delete(topic)
        session.commit()
        console.print(f"[green]Topic '{name}' deleted.[/green]")

@schedule_app.command("set")
def set_schedule(start: str, end: str):
    """Set notification schedule (HH:MM format)."""
    # Validate format
    try:
        datetime.strptime(start, "%H:%M")
        datetime.strptime(end, "%H:%M")
    except ValueError:
        console.print("[red]Invalid time format. Use HH:MM (e.g., 09:00).[/red]")
        return

    engine = get_engine()
    with Session(engine) as session:
        config = session.exec(select(UserConfig)).first()
        if not config:
            config = UserConfig(notification_start=start, notification_end=end)
        else:
            config.notification_start = start
            config.notification_end = end
            
        session.add(config)
        session.commit()
        console.print(f"[green]Schedule updated: Notifications active between {start} and {end}.[/green]")

@schedule_app.command("show")
def show_schedule():
    """Show current notification schedule."""
    engine = get_engine()
    with Session(engine) as session:
        config = session.exec(select(UserConfig)).first()
        if not config:
            # Create default if missing
            config = UserConfig()
            session.add(config)
            session.commit()
            
        console.print(f"Notifications are active between [bold]{config.notification_start}[/bold] and [bold]{config.notification_end}[/bold].")
