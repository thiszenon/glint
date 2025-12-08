"""Dev.to fetcher."""

from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic
from glint.core.config import config_manager
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class DevToFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Look back 30 days
        self.min_reactions = 10  # Minimum reactions (likes) to be considered
        self.base_url = "https://dev.to/api"

    @cached_fetch(ttl=180) # 3 minutes
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_articles = set()
        
        try:
            # Calculate cutoff time for last 30 days
            cutoff_time = datetime.now() - timedelta(days=self.days_back)
            
            if not topics:
                # No topics: fetch latest articles
                articles = self._fetch_articles(tag=None, per_page=30)
                trends.extend(self._process_articles(articles, None, cutoff_time, seen_articles))
            else:
                # Fetch articles for each topic
                for topic in topics:
                    # Dev.to uses tags, so we'll search by tag
                    articles = self._fetch_articles(tag=topic.name, per_page=20)
                    trends.extend(self._process_articles(articles, topic, cutoff_time, seen_articles))
                    
        except Exception as e:
            self.logger.error(f"Error fetching from Dev.to: {e}")
        
        return trends
    
    def _fetch_articles(self, tag: str = None, per_page: int = 30) -> list:
        """
        Fetch articles from Dev.to API.
        """
        articles = []
        
        try:
            # Dev.to API endpoint
            url = f"{self.base_url}/articles"
            
            params = {
                "per_page": per_page,
                "top": 30  # Get top articles from last 30 days
            }
            
            if tag:
                params["tag"] = tag
            
            # Use API key if available for higher rate limits
            headers = {'User-Agent': 'Glint/1.0 (Tech Watch Assistant)'}
            devto_key = config_manager.get_secret("devto")
            if devto_key:
                headers["api-key"] = devto_key
                self.logger.debug("Using Dev.to API key")
            
            response = self.http.get(
                url,
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                articles = response.json()
            elif response.status_code == 429:
                self.logger.warning("Dev.to rate limit hit")
                
        except Exception as e:
            self.logger.error(f"Error fetching Dev.to articles: {e}")
        
        return articles
    
    def _process_articles(
        self, 
        articles: list, 
        topic: Topic, 
        cutoff_time: datetime,
        seen_articles: set
    ) -> List[Trend]:
        """
        Process articles and convert to Trends.
        """
        trends = []
        
        for article in articles:
            article_id = article.get("id")
            
            # Skip duplicates
            if article_id in seen_articles:
                continue
            
            # Parse published date
            published_str = article.get("published_at", "")
            if published_str:
                # Dev.to uses ISO 8601 format
                published_at = datetime.strptime(
                    published_str.replace("Z", "+00:00").split("+")[0],
                    "%Y-%m-%dT%H:%M:%S"
                )
            else:
                continue
            
            # Check time filter
            if published_at < cutoff_time:
                continue
            
            # Quality filter
            if not self._is_quality_article(article):
                continue
            
            seen_articles.add(article_id)
            
            # Build trend
            trends.append(Trend(
                title=article.get("title", "Untitled"),
                description=self._build_description(article),
                url=article.get("url", ""),
                source="Dev.to",
                category=self._determine_category(article),
                published_at=published_at,
                topic_id=topic.id if topic else None
            ))
        
        return trends
    
    def _is_quality_article(self, article: dict) -> bool:
        """
        Filter out low-quality articles based on engagement.
        """
        reactions = article.get("public_reactions_count", 0)
        comments = article.get("comments_count", 0)
        reading_time = article.get("reading_time_minutes", 0)
        
        # Quality checks
        # Minimum engagement
        if reactions < self.min_reactions:
            return False
        
        # Prefer articles with discussion or high reactions
        if reactions < 30 and comments < 2:
            return False
        
        # Filter out very short articles (likely low quality)
        if reading_time < 2:
            return False
        
        return True
    
    def _build_description(self, article: dict) -> str:
        """
        Build description with key metrics.
        """
        description = article.get("description", "No description")
        reactions = article.get("public_reactions_count", 0)
        comments = article.get("comments_count", 0)
        reading_time = article.get("reading_time_minutes", 0)
        author = article.get("user", {}).get("name", "Unknown")
        
        # Format: "Description | ❤️ 234 | 💬 12 | ⏱ 5 min | by Author"
        metrics = f"❤️ {reactions} | 💬 {comments} | ⏱ {reading_time} min | by {author}"
        
        # Truncate description if too long
        if len(description) > 100:
            description = description[:100] + "..."
        
        return f"{description} | {metrics}"
    
    def _determine_category(self, article: dict) -> str:
        """
        Determine category based on article tags.
        """
        tags = [t.lower() for t in article.get("tag_list", [])]
        
        # Check for specific categories
        if any(t in tags for t in ["tutorial", "beginners", "learning"]):
            return "tutorial"
        elif any(t in tags for t in ["news", "discuss"]):
            return "news"
        elif any(t in tags for t in ["showdev", "opensource"]):
            return "project"
        elif any(t in tags for t in ["career", "productivity"]):
            return "career"
        else:
            return "article"
