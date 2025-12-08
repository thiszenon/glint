"""Reddit fetcher."""

import re
from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class RedditFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Look back 30 days
        self.min_upvotes = 10  # Minimum upvotes to be considered
        
        # Tech-focused subreddits mapped by general topics
        self.subreddit_map = {
            "programming": ["programming", "coding", "learnprogramming"],
            "python": ["python", "learnpython", "pythontips"],
            "javascript": ["javascript", "webdev", "node", "reactjs", "vuejs"],
            "web": ["webdev", "frontend", "backend", "fullstack"],
            "devops": ["devops", "docker", "kubernetes", "sysadmin"],
            "ai": ["MachineLearning", "artificial", "deeplearning", "datascience"],
            "rust": ["rust", "rustjerk"],
            "go": ["golang", "go"],
            "java": ["java", "javahelp"],
            "csharp": ["csharp", "dotnet"],
            "mobile": ["androiddev", "iOSProgramming", "reactnative", "flutter"],
            "gamedev": ["gamedev", "Unity3D", "unrealengine"],
            "security": ["netsec", "cybersecurity", "AskNetsec"],
            "linux": ["linux", "linuxquestions", "archlinux"],
            "database": ["database", "sql", "PostgreSQL", "mongodb"],
        }
        
        # Default subreddits for general tech news
        self.default_subreddits = ["programming", "webdev", "technology", "coding"]
    
    @cached_fetch(ttl=180) # 3 minutes
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_posts = set()  # Avoid duplicates
        
        try:
            # Calculate timestamp for last 30 days
            cutoff_time = datetime.now() - timedelta(days=self.days_back)
            
            # Determine which subreddits to fetch from
            subreddits_to_fetch = set()
            
            if not topics:
                # No topics: use default tech subreddits
                subreddits_to_fetch.update(self.default_subreddits)
            else:
                # Map topics to relevant subreddits
                for topic in topics:
                    topic_lower = topic.name.lower()
                    
                    # Direct match in subreddit map
                    if topic_lower in self.subreddit_map:
                        subreddits_to_fetch.update(self.subreddit_map[topic_lower])
                    else:
                        # Partial match (e.g., "react" matches "javascript")
                        for key, subs in self.subreddit_map.items():
                            if topic_lower in key or key in topic_lower:
                                subreddits_to_fetch.update(subs)
                        
                        # Also add default subreddits for broader coverage
                        subreddits_to_fetch.update(self.default_subreddits[:2])
            
            # Fetch from each subreddit
            for subreddit in subreddits_to_fetch:
                subreddit_trends = self._fetch_from_subreddit(
                    subreddit, 
                    topics, 
                    cutoff_time, 
                    seen_posts
                )
                trends.extend(subreddit_trends)
                
        except Exception as e:
            self.logger.error(f"Error fetching from Reddit: {e}")
        
        return trends
    
    def _fetch_from_subreddit(
        self, 
        subreddit: str, 
        topics: List[Topic], 
        cutoff_time: datetime,
        seen_posts: set
    ) -> List[Trend]:
        """
        Fetch posts from a specific subreddit.
        Uses Reddit's JSON API (no authentication needed for public posts).
        """
        trends = []
        
        try:
            # Reddit JSON API endpoints
            # We'll fetch from 'hot' and 'top' for better coverage
            endpoints = [
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
                f"https://www.reddit.com/r/{subreddit}/top.json?t=month&limit=25",
            ]
            
            for endpoint in endpoints:
                response = self.http.get(
                    endpoint,
                    headers={'User-Agent': 'Glint/1.0 (Tech Watch Assistant)'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])
                    
                    for post_wrapper in posts:
                        post = post_wrapper.get("data", {})
                        post_id = post.get("id")
                        
                        # Skip duplicates
                        if post_id in seen_posts:
                            continue
                        
                        # Check time filter
                        post_time = datetime.fromtimestamp(post.get("created_utc", 0))
                        if post_time < cutoff_time:
                            continue
                        
                        # Quality filter
                        if not self._is_quality_post(post):
                            continue
                        
                        # Topic matching
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")
                        matched_topic = self._match_topic(title, selftext, topics)
                        
                        # If we have topics, only add if matched
                        if topics and not matched_topic:
                            continue
                        
                        seen_posts.add(post_id)
                        
                        # Build trend
                        trends.append(Trend(
                            title=title,
                            description=self._build_description(post, subreddit),
                            url=self._get_post_url(post),
                            source="Reddit",
                            category=self._determine_category(post, subreddit),
                            published_at=post_time,
                            topic_id=matched_topic.id if matched_topic else None
                        ))
                        
                elif response.status_code == 429:
                    self.logger.warning(f"Reddit rate limit hit for r/{subreddit}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error fetching from r/{subreddit}: {e}")
        
        return trends
    
    def _is_quality_post(self, post: dict) -> bool:
        """
        Filter out low-quality posts based on engagement.
        """
        upvotes = post.get("ups", 0)
        num_comments = post.get("num_comments", 0)
        is_removed = post.get("removed_by_category") is not None
        is_deleted = post.get("author") == "[deleted]"
        
        # Quality checks
        if is_removed or is_deleted:
            return False
        
        # Minimum engagement
        if upvotes < self.min_upvotes:
            return False
        
        # Prefer posts with discussion (comments)
        # But allow highly upvoted posts even without comments
        if upvotes < 50 and num_comments < 2:
            return False
        
        return True
    
    def _match_topic(self, title: str, text: str, topics: List[Topic]):
        """
        Match post to a topic using similar logic to HackerNewsFetcher.
        """
        if not topics:
            return None
        
        title_lower = title.lower()
        text_lower = text.lower() if text else ""
        
        for topic in topics:
            topic_lower = topic.name.lower()
            pattern = rf'\b{re.escape(topic_lower)}\w*'
            
            if re.search(pattern, title_lower) or re.search(pattern, text_lower):
                return topic
        
        return None
    
    def _get_post_url(self, post: dict) -> str:
        """
        Get the best URL for the post.
        Prefer external links, fallback to Reddit discussion.
        """
        # If it's a link post, use the external URL
        if not post.get("is_self", False):
            return post.get("url", f"https://reddit.com{post.get('permalink', '')}")
        
        # For text posts, link to Reddit discussion
        return f"https://reddit.com{post.get('permalink', '')}"
    
    def _build_description(self, post: dict, subreddit: str) -> str:
        """
        Build description with engagement metrics.
        """
        upvotes = post.get("ups", 0)
        comments = post.get("num_comments", 0)
        author = post.get("author", "unknown")
        
        # Get preview text if available
        preview = ""
        if post.get("is_self", False):
            selftext = post.get("selftext", "")
            if selftext:
                # Truncate to first 100 chars
                preview = selftext[:100] + "..." if len(selftext) > 100 else selftext
                preview = preview.replace("\n", " ")
        
        # Format: "Preview | ⬆️ 234 | 💬 45 | r/programming"
        metrics = f"⬆️ {upvotes} | 💬 {comments} | r/{subreddit}"
        
        if preview:
            return f"{preview} | {metrics}"
        else:
            return metrics
    
    def _determine_category(self, post: dict, subreddit: str) -> str:
        """
        Determine category based on post flair and subreddit.
        """
        flair = post.get("link_flair_text", "").lower() if post.get("link_flair_text") else ""
        
        # Check flair for category hints
        if any(word in flair for word in ["tutorial", "guide", "learning"]):
            return "tutorial"
        elif any(word in flair for word in ["news", "article"]):
            return "news"
        elif any(word in flair for word in ["discussion", "question"]):
            return "discussion"
        elif any(word in flair for word in ["project", "showcase"]):
            return "project"
        
        # Fallback to subreddit-based categorization
        if subreddit in ["programming", "coding", "webdev"]:
            return "discussion"
        else:
            return "news"
