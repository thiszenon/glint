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
    def __init__(self):
        self.days_back = 30  # Configurable: look back 30 days
        self.min_stars = 50  # Minimum stars to be considered trending
        
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_repos = set()  # Avoid duplicates
        
        try:
            # Calculate date filter for last 30 days
            from datetime import timedelta
            date_filter = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
            
            if not topics:
                # If no topics, fetch general trending repos
                search_queries = [
                    (None, f"created:>{date_filter} stars:>{self.min_stars} sort:stars", "new_repo"),
                ]
            else:
                # For each topic, use multiple search strategies
                search_queries = []
                for topic in topics:
                    # Strategy 1: New repos with this topic (created in last 30 days)
                    search_queries.append((
                        topic, 
                        f"topic:{topic.name} created:>{date_filter} stars:>10 sort:stars",
                        "new_repo"
                    ))
                    
                    # Strategy 2: Trending repos (recently updated, high activity)
                    search_queries.append((
                        topic,
                        f"topic:{topic.name} pushed:>{date_filter} stars:>{self.min_stars} sort:stars",
                        "trending"
                    ))
                    
                    # Strategy 3: Keyword search in name/description (for broader matching)
                    search_queries.append((
                        topic,
                        f"{topic.name} in:name,description created:>{date_filter} stars:>10 sort:stars",
                        "keyword"
                    ))

            for topic, query, strategy in search_queries:
                url = f"https://api.github.com/search/repositories?q={query}&per_page=5"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        repo_id = item["id"]
                        
                        # Skip duplicates
                        if repo_id in seen_repos:
                            continue
                        seen_repos.add(repo_id)
                        
                        # Smart filtering: quality checks
                        if not self._is_quality_repo(item):
                            continue
                        
                        # Determine category based on strategy and repo characteristics
                        category = self._determine_category(item, strategy)
                        
                        # Enhanced description with metrics
                        description = self._build_description(item)
                        
                        trends.append(Trend(
                            title=item["full_name"],
                            description=description,
                            url=item["html_url"],
                            source="GitHub",
                            category=category,
                            published_at=datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                            topic_id=topic.id if topic else None
                        ))
                        
                elif response.status_code == 403:
                    # Rate limit hit
                    print(f"GitHub API rate limit exceeded. Try again later.")
                    break
                elif response.status_code != 404:
                    print(f"GitHub API error: {response.status_code}")
                    
        except Exception as ex:
            print(f"Error fetching from GitHub: {ex}")
        
        return trends
    
    def _is_quality_repo(self, repo: dict) -> bool:
        """
        Filter out low-quality repos based on multiple signals.
        """
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        open_issues = repo.get("open_issues_count", 0)
        has_description = bool(repo.get("description"))
        
        # Quality heuristics
        # 1. Must have a description
        if not has_description:
            return False
        
        # 2. Minimum engagement (stars or forks)
        if stars < 5 and forks < 2:
            return False
        
        # 3. Not abandoned (too many open issues relative to stars might indicate problems) à revoir
        if stars > 0 and open_issues / max(stars, 1) > 5:
            return False
        
        # 4. Not a fork (optional - you might want trending forks too)
        # if repo.get("fork", False):
        #     return False
        
        return True
    
    def _determine_category(self, repo: dict, strategy: str) -> str:
        """
        Determine the category based on repo characteristics.
        """
        topics = repo.get("topics", [])
        language = repo.get("language") or ""  # Handle None case
        language = language.lower()
        
        # Check for specific categories
        if any(t in topics for t in ["framework", "library", "api"]):
            return "framework"
        elif any(t in topics for t in ["tool", "cli", "devtools"]):
            return "tool"
        elif strategy == "new_repo":
            return "new_repo"
        elif strategy == "trending":
            return "trending"
        else:
            return "repo"
    
    def _build_description(self, repo: dict) -> str:
        """
        Build an enhanced description with key metrics.
        """
        desc = repo.get("description", "No description")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        language = repo.get("language", "Unknown")
        
        # Format: "Description |  1.2k |  234 | Python"
        metrics = f"{self._format_number(stars)} |{self._format_number(forks)} | {language}"
        
        return f"{desc} | {metrics}"
    
    def _format_number(self, num: int) -> str:
        """
        Format large numbers (e.g., 1234 -> 1.2k)
        """
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)

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

class RedditFetcher(BaseFetcher):
    def __init__(self):
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
    
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_posts = set()  # Avoid duplicates
        
        try:
            from datetime import timedelta
            import re
            
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
            print(f"Error fetching from Reddit: {e}")
        
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
                response = requests.get(
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
                    print(f"Reddit rate limit hit for r/{subreddit}")
                    break
                    
        except Exception as e:
            print(f"Error fetching from r/{subreddit}: {e}")
        
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
        
        import re
        
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

class ProductHuntFetcher(BaseFetcher):
    def __init__(self):
        self.days_back = 30  # Look back 30 days
        self.min_votes = 20  # Minimum upvotes to be considered
        
        # Product Hunt uses GraphQL API, but we can use their public REST-like endpoints
        # Note: For production, you might want to use their official API with token
        self.base_url = "https://www.producthunt.com/frontend/graphql"
        
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_products = set()
        
        try:
            from datetime import timedelta
            
            # Calculate date range for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_back)
            
            # Fetch products from the last 30 days
            # We'll iterate day by day for better coverage
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Fetch top products for this day
                products = self._fetch_day_products(date_str)
                
                for product in products:
                    product_id = product.get("id")
                    
                    # Skip duplicates
                    if product_id in seen_products:
                        continue
                    
                    # Quality filter
                    if not self._is_quality_product(product):
                        continue
                    
                    # Topic matching
                    matched_topic = self._match_topic(product, topics)
                    
                    # If we have topics, only add if matched
                    if topics and not matched_topic:
                        continue
                    
                    seen_products.add(product_id)
                    
                    # Build trend
                    trends.append(Trend(
                        title=product.get("name", "Unknown Product"),
                        description=self._build_description(product),
                        url=self._get_product_url(product),
                        source="Product Hunt",
                        category=self._determine_category(product),
                        published_at=datetime.strptime(
                            product.get("createdAt", current_date.isoformat()),
                            "%Y-%m-%dT%H:%M:%S.%fZ" if "." in product.get("createdAt", "") else "%Y-%m-%dT%H:%M:%SZ"
                        ) if "createdAt" in product else current_date,
                        topic_id=matched_topic.id if matched_topic else None
                    ))
                
                # Move to next day
                current_date += timedelta(days=1)
                
                # Limit to avoid too many requests (fetch every 3 days)
                current_date += timedelta(days=2)
                
        except Exception as e:
            print(f"Error fetching from Product Hunt: {e}")
        
        return trends
    
    def _fetch_day_products(self, date_str: str) -> list:
        """
        Fetch products for a specific day using Product Hunt's public API.
        Note: This uses a simplified approach. For production, use official API.
        """
        products = []
        
        try:
            # Product Hunt's public posts endpoint (no auth needed for basic access)
            # This is a simplified version - in production you'd use their GraphQL API
            url = f"https://api.producthunt.com/v2/api/graphql"
            
            # For now, we'll use a simpler approach: scrape the daily digest
            # In production, you should use official API with authentication
            # Using the public RSS feed as a fallback
            rss_url = "https://www.producthunt.com/feed"
            
            response = requests.get(
                rss_url,
                headers={'User-Agent': 'Glint/1.0 (Tech Watch Assistant)'}
            )
            
            if response.status_code == 200:
                # Parse RSS feed (simplified)
                # In production, use feedparser library
                import re
                
                # Extract product data from RSS
                # This is a basic implementation
                # For better results, use Product Hunt's official API
                
                # For now, return empty to avoid errors
                # TODO: Implement proper Product Hunt API integration
                pass
                
        except Exception as e:
            print(f"Error fetching Product Hunt data for {date_str}: {e}")
        
        return products
    
    def _is_quality_product(self, product: dict) -> bool:
        """
        Filter out low-quality products based on engagement.
        """
        votes = product.get("votesCount", 0)
        comments = product.get("commentsCount", 0)
        
        # Quality checks
        if votes < self.min_votes:
            return False
        
        # Prefer products with discussion
        if votes < 50 and comments < 3:
            return False
        
        return True
    
    def _match_topic(self, product: dict, topics: List[Topic]):
        """
        Match product to a topic based on name, tagline, and topics.
        """
        if not topics:
            return None
        
        import re
        
        name = product.get("name", "").lower()
        tagline = product.get("tagline", "").lower()
        description = product.get("description", "").lower()
        product_topics = [t.lower() for t in product.get("topics", [])]
        
        for topic in topics:
            topic_lower = topic.name.lower()
            pattern = rf'\b{re.escape(topic_lower)}\w*'
            
            # Check in name, tagline, description, or product topics
            if (re.search(pattern, name) or 
                re.search(pattern, tagline) or 
                re.search(pattern, description) or
                any(topic_lower in pt for pt in product_topics)):
                return topic
        
        return None
    
    def _get_product_url(self, product: dict) -> str:
        """
        Get the Product Hunt URL for the product.
        """
        slug = product.get("slug", "")
        if slug:
            return f"https://www.producthunt.com/posts/{slug}"
        return product.get("url", "https://www.producthunt.com")
    
    def _build_description(self, product: dict) -> str:
        """
        Build description with key metrics.
        """
        tagline = product.get("tagline", "No tagline")
        votes = product.get("votesCount", 0)
        comments = product.get("commentsCount", 0)
        
        # Format: "Tagline |  234 votes |  12 comments"
        metrics = f" {votes} votes | {comments} comments"
        
        return f"{tagline} | {metrics}"
    
    def _determine_category(self, product: dict) -> str:
        """
        Determine category based on product topics.
        """
        topics = [t.lower() for t in product.get("topics", [])]
        
        # Check for specific categories
        if any(t in topics for t in ["developer tools", "api", "open source"]):
            return "tool"
        elif any(t in topics for t in ["productivity", "saas"]):
            return "saas"
        elif any(t in topics for t in ["design", "ui", "ux"]):
            return "design"
        else:
            return "product"

class DevToFetcher(BaseFetcher):
    def __init__(self):
        self.days_back = 30  # Look back 30 days
        self.min_reactions = 10  # Minimum reactions (likes) to be considered
        self.base_url = "https://dev.to/api"
        
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_articles = set()
        
        try:
            from datetime import timedelta
            
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
            print(f"Error fetching from Dev.to: {e}")
        
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
            
            response = requests.get(
                url,
                params=params,
                headers={'User-Agent': 'Glint/1.0 (Tech Watch Assistant)'}
            )
            
            if response.status_code == 200:
                articles = response.json()
            elif response.status_code == 429:
                print("Dev.to rate limit hit")
                
        except Exception as e:
            print(f"Error fetching Dev.to articles: {e}")
        
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
        
        # Format: "Description |  234 | 12 | 5 min | by Author"
        metrics = f" {reactions} |  {comments} |  {reading_time} min | by {author}"
        
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


