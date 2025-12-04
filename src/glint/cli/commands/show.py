import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic, UserActivity
import webbrowser
from datetime import datetime

console = Console()
app = typer.Typer()

@app.command()
def show(
    limit: int = typer.Option(20, help="Number of trends to show"),
    topic: str = typer.Option(None, help="Filter by topic name"),
    unread: bool = typer.Option(False, help="Show only unread trends"),
    sort_by: str = typer.Option(
        "relevance", 
        help="Sort by: 'relevance' (best match), 'recent' (recently found), 'date' (recently published)"
    )
):
    """Display latest trends in a table."""
    engine = get_engine()
    
    with Session(engine) as session:
        # Build query
        query = select(Trend).where(Trend.status == "approved")

        # Apply sorting based on user choice
        if sort_by == "recent":
            # Sort by when Glint discovered the trend
            query = query.order_by(Trend.fetched_at.desc())
        elif sort_by == "date":
            # Sort by when the content was published
            query = query.order_by(Trend.published_at.desc())
        else:  # Default: relevance
            # Sort by relevance score (best matches first)
            query = query.order_by(Trend.relevance_score.desc())
        
        # Apply filters
        if topic:
            query = query.where(Trend.topic.has(Topic.name == topic))
        if unread:
            query = query.where(Trend.is_read == False)
        
        query = query.limit(limit)
        
        results = session.exec(query).all()
        
        if not results:
            console.print("[yellow]No trends found.[/yellow]")
            console.print("Try running: [bold]glint fetch[/bold]")
            return
        
        # Display table with sort indicator
        sort_labels = {
            "relevance": "by Relevance Score",
            "recent": "by Recently Found",
            "date": "by Published Date"
        }
        sort_label = sort_labels.get(sort_by, "by Relevance")
        table = Table(title=f"Latest {len(results)} Trends (Sorted {sort_label})", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="bold", ratio=3,no_wrap=True,overflow="ellipsis")
        table.add_column("Source", style="magenta", ratio=1)
        table.add_column("Topic", style="green", ratio=1)
        table.add_column("Date", style="blue", width=10)
        table.add_column("Read", style="yellow", width=6)
        
        trends_list = []
        for idx, trend in enumerate(results, 1):
            trends_list.append(trend)
            
            # Truncate title if too long
            title = trend.title[:47] + "..." if len(trend.title) > 50 else trend.title
            
            # Format date
            date_str = trend.published_at.strftime("%Y-%m-%d")
            
            # Read status
            read_status = "✓" if trend.is_read else "✗"

            #get topic name from the trend's topic relationship
            topic_name = session.get(Topic, trend.topic_id).name if trend.topic_id else "N/A"

            
            table.add_row(
                str(idx),
                title,
                trend.source,
                topic_name,
                date_str,
                read_status
            )
        
        console.print(table)
        console.print()
        
        # Interactive selection
        console.print("[bold]Enter a number to open the trend, or 'q' to quit:[/bold]")
        
        while True:
            choice = Prompt.ask("Select", default="q")
            
            if choice.lower() == 'q':
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(trends_list):
                    trend = trends_list[idx]
                    
                    # Log activity
                    activity = UserActivity(
                        trend_id=trend.id,
                        clicked_at=datetime.utcnow()
                    )
                    session.add(activity)
                    
                    # Mark as read
                    trend.is_read = True
                    session.add(trend)
                    session.commit()
                    
                    # Open in browser
                    console.print(f"[green]Opening:[/green] {trend.url}")
                    webbrowser.open(trend.url)
                    
                    console.print("[dim]Marked as read ✓[/dim]")
                    console.print()
                else:
                    console.print("[red]Invalid number. Try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number or 'q'.[/red]")

if __name__ == "__main__":
    app()
