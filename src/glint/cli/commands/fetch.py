import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic
from glint.core.fetchers import GitHubFetcher, HackerNewsFetcher, RedditFetcher, DevToFetcher

console = Console()
app = typer.Typer()

@app.command()
def fetch():
    """
    Fetch the latest tech trends for watched topics.
    """
    console.print("[bold blue]Fetching latest tech trends...[/bold blue]")
    
    # Note: ProductHuntFetcher needs API implementation, skipping for now
    fetchers = [GitHubFetcher(), HackerNewsFetcher(), RedditFetcher(), DevToFetcher()]
    new_trends_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Connecting to sources...", total=None)
        
        engine = get_engine()
        with Session(engine) as session:
            # Get ALL topics (active and inactive) - inactive topics are in "standby mode"
            # They still get data fetched, but won't be displayed or notified about
            all_topics = session.exec(select(Topic)).all()
            
            for fetcher in fetchers:
                source_name = fetcher.__class__.__name__.replace("Fetcher", "")
                progress.update(task, description=f"Fetching from {source_name}...")
                
                try:
                    trends = fetcher.fetch(all_topics)
                    for trend in trends:
                        # Check for duplicates based on URL
                        statement = select(Trend).where(Trend.url == trend.url)
                        results = session.exec(statement)
                        existing_trend = results.first()
                        
                        if not existing_trend:
                            session.add(trend)
                            new_trends_count += 1
                except Exception as e:
                    console.print(f"[red]Error fetching from {source_name}: {e}[/red]")
            
            session.commit()
            
    if new_trends_count > 0:
        console.print(f"[green]Fetch complete! Added {new_trends_count} new trends.[/green]")
    else:
        console.print("[dim]Fetch complete. No new trends found.[/dim]")
