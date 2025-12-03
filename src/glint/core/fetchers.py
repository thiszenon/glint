"""
Fetchers module - imports all fetcher classes from sources.

This module maintains backward compatibility by re-exporting all fetcher classes.
The actual implementations are now in the glint.sources package.
"""

from glint.sources import (
    BaseFetcher,
    GitHubFetcher,
    HackerNewsFetcher,
    RedditFetcher,
    DevToFetcher,
    ProductHuntFetcher,
)

__all__ = [
    "BaseFetcher",
    "GitHubFetcher",
    "HackerNewsFetcher",
    "RedditFetcher",
    "DevToFetcher",
    "ProductHuntFetcher",
]
