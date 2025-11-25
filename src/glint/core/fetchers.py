import requests
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from glint.core.models import Trend, Topic

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        pass

class GitHubFetcher(BaseFetcher):
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        try:
            # If no topics, default to general trending (or skip)
            # For now, let's just search for "stars" if no topics, or maybe just return empty?
            # Let's default to a general search if no topics are provided to keep existing behavior
            search_queries = []
            if not topics:
                search_queries.append((None, "created:>2023-01-01 sort:stars"))
            else:
                for topic in topics:
                    # Search for repos with this topic
                    search_queries.append((topic, f"topic:{topic.name} created:>2023-01-01 sort:stars"))

            for topic, query in search_queries:
                url = f"https://api.github.com/search/repositories?q={query}&per_page=5"
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
                            published_at=datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                            topic_id=topic.id if topic else None
                        ))
        except Exception as e:
            print(f"Error fetching from GitHub: {e}")
        return trends

class HackerNewsFetcher(BaseFetcher):
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        try:
            # Get top stories IDs
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url)
            if response.status_code == 200:
                ids = response.json()[:10] # Get top 10 to have better chance of matching topics
                
                for id in ids:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
                    item_resp = requests.get(item_url)
                    if item_resp.status_code == 200:
                        item = item_resp.json()
                        if "url" in item: # Only stories with URLs
                            title = item.get("title", "No Title")
                            
                            # Simple keyword matching for topics
                            matched_topic_id = None
                            if topics:
                                for topic in topics:
                                    if topic.name.lower() in title.lower():
                                        matched_topic_id = topic.id
                                        break
                            
                            trends.append(Trend(
                                title=title,
                                description=f"Score: {item.get('score', 0)} by {item.get('by', 'unknown')}",
                                url=item.get("url", ""),
                                source="Hacker News",
                                category="news",
                                published_at=datetime.fromtimestamp(item.get("time", 0)),
                                topic_id=matched_topic_id
                            ))
        except Exception as e:
            print(f"Error fetching from Hacker News: {e}")
        return trends
