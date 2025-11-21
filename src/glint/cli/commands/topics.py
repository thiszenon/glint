import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Topic

console = Console()
app = typer.Typer()

@app.command()
def add(topic_name: str):
    """
    Add a new topic to watch.
    """
    try:
        engine = get_engine()
        with Session(engine) as session:
            # Check if exists
            existing = session.exec(select(Topic).where(Topic.name == topic_name)).first()
            if existing:
                console.print(f"[yellow]Topic '{topic_name}' is already being watched.[/yellow]")
                return
            
            # Create new
            topic = Topic(name=topic_name)
            session.add(topic)
            session.commit()
            console.print(f"[green]Added topic: {topic_name}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error adding topic: {e}[/red]")

@app.command("list")
def list_topics():
    """
    List all watched topics.
    """
    try:
        engine = get_engine()
        with Session(engine) as session:
            topics = session.exec(select(Topic)).all()
            
            if not topics:
                console.print("[yellow]No topics found. Add one with `glint add <topic>`[/yellow]")
                return

            table = Table(title="Watched Topics")
            table.add_column("ID", style="dim")
            table.add_column("Topic", style="cyan")
            table.add_column("Active", style="green")
            
            for topic in topics:
                table.add_row(str(topic.id), topic.name, "Yes" if topic.is_active else "No")
                
            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing topics: {e}[/red]")
