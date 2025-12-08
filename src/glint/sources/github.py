"""GitHub repository fetcher."""

from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic
from glint.core.config import config_manager
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class GitHubFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Configurable: look back 30 days
        self.min_stars = 50  # Minimum stars to be considered trending
      
    @cached_fetch(ttl=180) # 3 minutes
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_repos = set()  # Avoid duplicates
        
        try:
            # Calculate date filter for last 30 days
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
                
                # Use API token if available for higher rate limits
                headers = {}
                github_token = config_manager.get_secret("github_token")
                if github_token:
                    headers["Authorization"] = f"token {github_token}"
                    self.logger.debug("Using GitHub API token")
                
                response = self.http.get(url, headers=headers)
                
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
                    self.logger.warning(f"GitHub API rate limit exceeded.")
                    break
                elif response.status_code != 404:
                    self.logger.error(f"GitHub API error: {response.status_code}")
                    
        except Exception as ex:
            self.logger.error(f"Error fetching from GitHub: {ex}")
        
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
        
        # 3. Not abandoned (too many open issues relative to stars might indicate problems)
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
        
        # Format: "Description | ⭐ 1.2k | 🍴 234 | Python"
        metrics = f"{self._format_number(stars)} |{self._format_number(forks)} | {language}"
        
        return f"{desc} | {metrics}"
    
    def _format_number(self, num: int) -> str:
        """
        Format large numbers (e.g., 1234 -> 1.2k)
        """
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)
