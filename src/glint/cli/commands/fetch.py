import typer
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic
from glint.core.parallel_fetcher import ParallelFetcher 
from glint.utils.url_utils import normalize_url 
from glint.utils.relevance import calculate_relevance
from glint.utils.fingerprint import generate_fingerprint


console = Console()
app = typer.Typer()

@app.command()
def fetch():
    """
    Fetch the latest tech trends for watched topics.
    """
    console.print("[bold blue]Fetching latest tech trends...[/bold blue]")

    #create parallel fetcher
    coordinator = ParallelFetcher()
    new_trends_count = 0

    engine = get_engine()

    with Session(engine) as session:
        # Get ALL topics (active and inactive) - inactive topics are in "standby mode"
        all_topics = session.exec(select(Topic)).all()
        
        if not all_topics:
            console.print("[yellow]No topics configured. Use 'glint add <topic>' to add some.[/yellow]")
            return
        
        # Progress bar for parallel fetch
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Fetching from all sources ...", total=None)
            
            # Measure fetch time
            start_time = time.time()
            
            # PARALLEL FETCH - All sources at once!
            all_trends = coordinator.fetch_all(all_topics)
            
            elapsed_time = time.time() - start_time
            
            progress.update(task, description="Processing and deduplicating trends...")
            
            # Process all fetched trends (deduplication, scoring)
            for trend in all_trends:
                # Normalize URL
                normalized_url = normalize_url(trend.url)
                
                # Check for URL duplicates
                existing_trend = session.exec(
                    select(Trend).where(Trend.url_normalized == normalized_url)
                ).first()
                
                if not existing_trend:
                    # Store normalized URL
                    trend.url_normalized = normalized_url
                    
                    # Generate fingerprint
                    trend.content_fingerprint = generate_fingerprint(
                        trend.title,
                        trend.description
                    )
                    
                    # Check for content duplicates
                    fingerprint_match = session.exec(
                        select(Trend).where(
                            Trend.content_fingerprint == trend.content_fingerprint
                        )
                    ).first()
                    
                    if not fingerprint_match:
                        # Find which topic this trend matched
                        matched_topic = None
                        for topic in all_topics:
                            if trend.topic_id == topic.id:
                                matched_topic = topic
                                break
                        
                        if matched_topic:
                            # Calculate relevance score
                            trend.relevance_score = calculate_relevance(trend, matched_topic)
                            
                            # Set status based on score threshold
                            if trend.relevance_score >= 0.3:
                                trend.status = "approved"
                            else:
                                trend.status = "rejected"
                        else:
                            trend.relevance_score = 0.0
                            trend.status = "rejected"
                        
                        # Save ALL trends (approved or rejected)
                        session.add(trend)
                        new_trends_count += 1
        
        # Commit all at once (faster than individual commits)
        session.commit()
    
    # Show results with timing
    if new_trends_count > 0:
        console.print(f"[green]✓ Fetch complete in {elapsed_time:.1f}s![/green]")
        console.print(f"[green]✓ Added {new_trends_count} new trends to database[/green]")
    else:
        console.print(f"[dim]Fetch complete in {elapsed_time:.1f}s. No new trends found.[/dim]")