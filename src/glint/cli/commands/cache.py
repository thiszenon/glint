import typer
from rich.console import Console
from glint.utils.cache import trend_cache


app = typer.Typer()
console = Console()

@app.command()
def clear():
    """Clear the trend cache"""
    trend_cache.clear()
    console.print("[green]Cache cleared successfully[/green]")
#end clear

@app.command()
def stats():
    """show cache statistics"""
    cache_size = len(trend_cache._cache)
    console.print(f"Cache entries: {cache_size}")
    console.print(f"TIME TO LIVE: {trend_cache._ttl} seconds")