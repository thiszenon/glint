import requests
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from glint.core.models import Trend

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self) -> List[Trend]:
        pass

class GitHubFetcher(BaseFetcher):
    def fetch(self) -> List[Trend]:
        trends = []
        try:
            # Search for popular repos created in the last 30 days
            # This is a rough approximation of "trending"
            # Ideally we'd scrape the trending page but that's harder to maintain
            url = "https://api.github.com/search/repositories?q=created:>2023-01-01&sort=stars&order=desc&per_page=5"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    trends.append(Trend(
                        title=item["full_name"],
                        description=item["description"] or "No description",
                        url=item["html_url"],
                        source="GitHub",
                        category="repo",
                        published_at=datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                    ))
        except Exception as e:
            print(f"Error fetching from GitHub: {e}")
        return trends

class HackerNewsFetcher(BaseFetcher):
    def fetch(self) -> List[Trend]:
        trends = []
        try:
            # Get top stories IDs
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url)
            if response.status_code == 200:
                ids = response.json()[:5] # Get top 5
                
                for id in ids:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
                    item_resp = requests.get(item_url)
                    if item_resp.status_code == 200:
                        item = item_resp.json()
                        if "url" in item: # Only stories with URLs
                            trends.append(Trend(
                                title=item.get("title", "No Title"),
                                description=f"Score: {item.get('score', 0)} by {item.get('by', 'unknown')}",
                                url=item.get("url", ""),
                                source="Hacker News",
                                category="news",
                                published_at=datetime.fromtimestamp(item.get("time", 0))
                            ))
        except Exception as e:
            print(f"Error fetching from Hacker News: {e}")
        return trends
