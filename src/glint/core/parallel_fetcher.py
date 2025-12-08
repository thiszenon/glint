from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from glint.core.models import Topic, Trend
from glint.sources import (
    GitHubFetcher, HackerNewsFetcher, RedditFetcher, DevToFetcher,
    ArXivFetcher, SemanticScholarFetcher, OpenAlexFetcher
)

class ParallelFetcher:
    def __init__(self):
        self.fetchers = [
            # Developer sources
            GitHubFetcher(),
            HackerNewsFetcher(),
            RedditFetcher(),
            DevToFetcher(),
            # Scientific sources
            ArXivFetcher(),
            SemanticScholarFetcher(),
            OpenAlexFetcher(),
        ]
        self.max_workers = len(self.fetchers)
    #end __init__

    def fetch_all(self, topics: List[Topic]) -> List[Trend]:
        """Fetch from all sources in parallel"""
        all_trends = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            #submit all fetch tasks
            future_to_fetcher = {
                executor.submit(fetcher.fetch, topics): fetcher
                for fetcher in self.fetchers
            }

            #collect results as they complete
            for future in as_completed(future_to_fetcher):
                fetcher = future_to_fetcher[future]
                try:
                    trends = future.result(timeout=60)
                    all_trends.extend(trends)
                    print(f"✓ {fetcher.__class__.__name__}: {len(trends)} trends")
                except Exception as ex:
                    print(f"✗ {fetcher.__class__.__name__}: {ex}")
        return all_trends
    #end fetch_all