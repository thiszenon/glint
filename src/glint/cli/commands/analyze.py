"""Analysis commands for debugging and tuning."""

import typer
import csv
from pathlib import Path
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select, func
from glint.core.database import get_engine
from glint.core.models import Trend, Topic

app = typer.Typer()
console = Console()


@app.command()
def rejected(
    output: str = typer.Option("rejected_trends.csv", help="Output CSV file path"),
    limit: int = typer.Option(None, help="Limit number of trends to export")
):
    """
    Export rejected trends to CSV for analysis.
    
    This helps you:
    - See which trends are being filtered out
    - Adjust your scoring threshold (0.3)
    - Find false negatives (good content rejected)
    - Improve negative keywords
    """
    engine = get_engine()
    
    with Session(engine) as session:
        # Get all rejected trends
        statement = select(Trend).where(Trend.status == "rejected")
        statement = statement.order_by(Trend.relevance_score.desc())
        
        if limit:
            statement = statement.limit(limit)
        
        rejected_trends = session.exec(statement).all()
        
        if not rejected_trends:
            console.print("[yellow]No rejected trends found.[/yellow]")
            console.print("All trends are approved! ")
            return
        
        # Get topics for lookup
        topics = session.exec(select(Topic)).all()
        topic_map = {topic.id: topic.name for topic in topics}
        
        # Write to CSV
        output_path = Path(output)
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'Title', 
                'Source', 
                'Topic', 
                'Score', 
                'Published Date', 
                'URL'
            ])
            
            # Data
            for trend in rejected_trends:
                topic_name = topic_map.get(trend.topic_id, "Unknown")
                writer.writerow([
                    trend.title,
                    trend.source,
                    topic_name,
                    f"{trend.relevance_score:.3f}" if trend.relevance_score else "0.000",
                    trend.published_at.strftime("%Y-%m-%d") if trend.published_at else "N/A",
                    trend.url
                ])
        
        console.print(f"[green] Exported {len(rejected_trends)} rejected trends to {output_path}[/green]")
        console.print(f"\n[dim]Open with: {output_path}[/dim]")


@app.command()
def stats():
    """
    Show statistics about trend approval/rejection.
    
    Displays:
    - Approval rate by source
    - Approval rate by topic
    - Score distribution
    """
    engine = get_engine()
    
    with Session(engine) as session:
        # Overall stats
        total = session.exec(select(func.count(Trend.id))).one()
        approved = session.exec(select(func.count(Trend.id)).where(Trend.status == "approved")).one()
        rejected = session.exec(select(func.count(Trend.id)).where(Trend.status == "rejected")).one()
        
        console.print("\n[bold] Overall Statistics[/bold]")
        console.print(f"  Total trends: {total}")
        console.print(f"  Approved: {approved} ({approved/total*100:.1f}%)")
        console.print(f"  Rejected: {rejected} ({rejected/total*100:.1f}%)")
        
        # By source
        console.print("\n[bold] By Source[/bold]")
        sources = session.exec(select(Trend.source).distinct()).all()
        
        source_table = Table(show_header=True)
        source_table.add_column("Source", style="cyan")
        source_table.add_column("Approved", style="green")
        source_table.add_column("Rejected", style="red")
        source_table.add_column("Rate", style="yellow")
        
        for source in sources:
            total_source = session.exec(
                select(func.count(Trend.id)).where(Trend.source == source)
            ).one()
            approved_source = session.exec(
                select(func.count(Trend.id)).where(
                    Trend.source == source, 
                    Trend.status == "approved"
                )
            ).one()
            rejected_source = total_source - approved_source
            rate = approved_source / total_source * 100 if total_source > 0 else 0
            
            source_table.add_row(
                source,
                str(approved_source),
                str(rejected_source),
                f"{rate:.1f}%"
            )
        
        console.print(source_table)
        
        # By topic
        console.print("\n[bold] By Topic[/bold]")
        topics = session.exec(select(Topic)).all()
        
        topic_table = Table(show_header=True)
        topic_table.add_column("Topic", style="cyan")
        topic_table.add_column("Approved", style="green")
        topic_table.add_column("Rejected", style="red")
        topic_table.add_column("Rate", style="yellow")
        
        for topic in topics:
            total_topic = session.exec(
                select(func.count(Trend.id)).where(Trend.topic_id == topic.id)
            ).one()
            approved_topic = session.exec(
                select(func.count(Trend.id)).where(
                    Trend.topic_id == topic.id,
                    Trend.status == "approved"
                )
            ).one()
            rejected_topic = total_topic - approved_topic
            rate = approved_topic / total_topic * 100 if total_topic > 0 else 0
            
            topic_table.add_row(
                topic.name,
                str(approved_topic),
                str(rejected_topic),
                f"{rate:.1f}%"
            )
        
        console.print(topic_table)


if __name__ == "__main__":
    app()
