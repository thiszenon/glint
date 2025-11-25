import typer
from rich.console import Console
from rich.panel import Panel
from sqlmodel import Session, select, func
from glint.core.database import get_engine, get_db_path
from glint.core.models import Topic, Trend
import os

console = Console()
app = typer.Typer()

@app.command()
def status():
    """
    Show current status and configuration.
    """
    try:
        engine = get_engine()
        db_path = get_db_path()
        
        with Session(engine) as session:
            # Get counts
            topic_count = session.exec(select(func.count(Topic.id))).one()
            trend_count = session.exec(select(func.count(Trend.id))).one()
            unread_count = session.exec(select(func.count(Trend.id)).where(Trend.is_read == False)).one()
            last_fetch_time = session.exec(select(Trend.fetched_at).order_by(Trend.fetched_at.desc()).limit(1)).one()
            
            # Get DB size
            db_size = 0
            if db_path.exists():
                db_size = os.path.getsize(db_path) / 1024 # KB

            console.print(Panel.fit(
                f"[bold green]Glint Status[/bold green]\n\n"
                f"[blue]Topics Watched:[/blue] {topic_count}\n"
                f"[blue]Total Trends:[/blue] {trend_count}\n"
                f"[blue]Unread Trends:[/blue] {unread_count}\n"
                f"[blue]Database Size:[/blue] {db_size:.2f} KB\n"
                f"[blue]Last Fetch:[/blue] {last_fetch_time}\n"
                f"[blue]Storage:[/blue] {db_path}",
                border_style="green"
            ))
            
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
