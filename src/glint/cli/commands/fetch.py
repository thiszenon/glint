import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend, Topic
from glint.core.fetchers import GitHubFetcher, HackerNewsFetcher, RedditFetcher, DevToFetcher
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
                        #TODO:NORMALIZE URL FUNCTION
                        normalized_url = normalize_url(trend.url)
                        #check for duplicates
                        statement = select(Trend).where(Trend.url_normalized == normalized_url)
                        results = session.exec(statement)
                        existing_trend = results.first()

                        if not existing_trend:
                            #store normalized URL
                            trend.url_normalized = normalized_url

                            #generate fingerprint
                            trend.content_fingerprint = generate_fingerprint(
                                trend.title,
                                trend.description
                            )

                            #check for content duplicates
                            fingerprint_statement = select(Trend).where(
                                Trend.content_fingerprint == trend.content_fingerprint
                            )

                            fingerprint_match = session.exec(fingerprint_statement).first()

                            if not fingerprint_match:
                                #calculate relevance score
                                #find which topic this trend matched
                                matched_topic = None
                                for topic in all_topics:
                                    if trend.topic_id == topic.id:
                                        matched_topic = topic
                                        break
                                if matched_topic:
                                    #calculate and store score
                                    trend.relevance_score = calculate_relevance(trend,matched_topic)

                                    #set status based on score threshold
                                    if trend.relevance_score >= 0.3:
                                        trend.status = "approved"
                                    else:
                                        trend.status = "rejected"
                                else:
                                    trend.relevance_score = 0.0
                                    trend.status = "rejected"
                            #save ALL trends (approved or rejected)
                            session.add(trend)
                            new_trends_count +=1  
                        else:
                            # content duplicate found -skip 
                            pass
                except Exception as e:
                    console.print(f"[red]Error fetching from {source_name}: {e}[/red]")
            
            session.commit()
            
    if new_trends_count > 0:
        console.print(f"[green]Fetch complete! Added {new_trends_count} new trends.[/green]")
    else:
        console.print("[dim]Fetch complete. No new trends found.[/dim]")
