"""Product Hunt fetcher."""

import re
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from glint.core.models import Trend, Topic
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class ProductHuntFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 7  # Look back 7 days (RSS feed is limited)
        self.min_votes = 20  # Minimum upvotes to be considered
    
    @cached_fetch(ttl=180) # 3 minutes
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_products = set()
        
        try:
            # Use Product Hunt's public RSS feed (no authentication required)
            rss_url = "https://www.producthunt.com/feed"
            
            response = self.http.get(
                rss_url,
                headers={'User-Agent': 'Glint/1.0 (Tech Watch Assistant)'},
                timeout=10
            )
            
            if response.status_code == 200:
                # Parse RSS feed
                root = ET.fromstring(response.content)
                cutoff_time = datetime.now() - timedelta(days=self.days_back)
                
                # Find all items in the feed
                for item in root.findall('.//item'):
                    try:
                        title = item.find('title').text if item.find('title') is not None else "Unknown Product"
                        link = item.find('link').text if item.find('link') is not None else ""
                        description = item.find('description').text if item.find('description') is not None else ""
                        pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ""
                        
                        # Parse date (RSS date format: "Mon, 01 Jan 2024 12:00:00 +0000")
                        if pub_date_str:
                            pub_date = parsedate_to_datetime(pub_date_str)
                        else:
                            pub_date = datetime.now()
                        
                        # Check if within time range
                        if pub_date < cutoff_time:
                            continue
                        
                        # Skip duplicates
                        if link in seen_products:
                            continue
                        seen_products.add(link)
                        
                        # Topic matching (check title and description)
                        matched_topic = self._match_topic(title, description, topics)
                        
                        # If we have topics, only add if matched
                        if topics and not matched_topic:
                            continue
                        
                        # Build trend
                        trends.append(Trend(
                            title=title,
                            description=description[:200] if description else "No description",
                            url=link,
                            source="Product Hunt",
                            category="product",
                            published_at=pub_date,
                            topic_id=matched_topic.id if matched_topic else None
                        ))
                        
                    except Exception as e:
                        self.logger.debug(f"Error parsing Product Hunt item: {e}")
                        continue
                        
            elif response.status_code == 429:
                self.logger.warning("Product Hunt rate limit hit")
            else:
                self.logger.error(f"Product Hunt error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error fetching from Product Hunt: {e}")
        
        return trends
    
    def _match_topic(self, title: str, description: str, topics: List[Topic]):
        """Match product to a topic based on title and description."""
        if not topics:
            return None
        
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        for topic in topics:
            topic_lower = topic.name.lower()
            pattern = rf'\b{re.escape(topic_lower)}\w*'
            
            if re.search(pattern, title_lower) or re.search(pattern, desc_lower):
                return topic
        
        return None
