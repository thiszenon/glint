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
                    # a verifier pour une bonne logique de recherche et news.
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
        
        # If no active topics, return empty list (Option 2: strict filtering)
        if not topics:
            return trends
        
        try:
            # Get top stories IDs - fetch more to increase match chances
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url)
            if response.status_code == 200:
                ids = response.json()[:30]  # Fetch top 30 instead of 10
                
                for id in ids:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
                    item_resp = requests.get(item_url)
                    if item_resp.status_code == 200:
                        item = item_resp.json()
                        if "url" in item:  # Only stories with URLs
                            title = item.get("title", "No Title")
                            text = item.get("text", "")  # Get story text if available
                            
                            # Improved keyword matching for topics
                            matched_topic = None
                            for topic in topics:
                                if self._matches_topic(topic.name, title, text):
                                    matched_topic = topic
                                    break
                            
                            # Only add trend if it matches a watched topic (Option 2)
                            if matched_topic:
                                trends.append(Trend(
                                    title=title,
                                    description=f"Score: {item.get('score', 0)} by {item.get('by', 'unknown')}",
                                    url=item.get("url", ""),
                                    source="Hacker News",
                                    category="news",
                                    published_at=datetime.fromtimestamp(item.get("time", 0)),
                                    topic_id=matched_topic.id
                                ))
        except Exception as e:
            print(f"Error fetching from Hacker News: {e}")
        return trends
    
    def _matches_topic(self, topic_name: str, title: str, text: str) -> bool:
        """
        Improved matching logic:
        - Checks both title and text
        - Uses partial word matching (e.g., 'react' matches 'reactjs', 'react-native')
        - Case-insensitive
        """
        topic_lower = topic_name.lower()
        title_lower = title.lower()
        text_lower = text.lower() if text else ""
        
        # Check if topic appears as a whole word or part of a compound word
        # This handles cases like: "python" matches "python3", "pythonic"
        # "react" matches "reactjs", "react-native"
        import re
        pattern = rf'\b{re.escape(topic_lower)}\w*'
        
        if re.search(pattern, title_lower) or re.search(pattern, text_lower):
            return True
        
        return False
