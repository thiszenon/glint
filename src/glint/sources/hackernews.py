"""Hacker News fetcher."""

import re
import requests
from typing import List
from datetime import datetime
from glint.core.models import Trend, Topic
from glint.sources.base import BaseFetcher


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
            self.logger.error(f"Error fetching from Hacker News: {e}")
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
        pattern = rf'\b{re.escape(topic_lower)}\w*'
        
        if re.search(pattern, title_lower) or re.search(pattern, text_lower):
            return True
        
        return False
