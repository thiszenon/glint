"""OpenAlex fetcher for broad academic research coverage."""

from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class OpenAlexFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Look back 30 days
        self.max_results = 20  # Results per topic
        self.base_url = "https://api.openalex.org/works"
        self.min_citations = 3  # Minimum citations for quality
    
    @cached_fetch(ttl=600)  # 10 minutes cache
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_ids = set()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.days_back)
            date_filter = cutoff_date.strftime("%Y-%m-%d")
            
            if not topics:
                # No topics: fetch recent impactful works
                works = self._search_works("computer science", date_filter)
                trends.extend(self._process_works(works, None, seen_ids))
            else:
                # Fetch for each topic
                for topic in topics:
                    works = self._search_works(topic.name, date_filter)
                    trends.extend(self._process_works(works, topic, seen_ids))
                    
        except Exception as e:
            self.logger.error(f"Error fetching from OpenAlex: {e}")
        
        return trends
    
    def _search_works(self, query: str, from_date: str) -> List[dict]:
        """Search for works using OpenAlex API"""
        try:
            # Build filter
            # Format: from_publication_date:2024-01-01,default.search:query
            params = {
                "filter": f"from_publication_date:{from_date},default.search:{query}",
                "per-page": self.max_results,
                "sort": "cited_by_count:desc",  # Sort by citations
                "mailto": "glint@example.com"  # Polite pool (faster rate limits)
            }
            
            response = self.http.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            elif response.status_code == 429:
                self.logger.warning("OpenAlex rate limit hit")
            else:
                self.logger.warning(f"OpenAlex API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error searching OpenAlex: {e}")
        
        return []
    
    def _process_works(
        self, 
        works: List[dict], 
        topic: Topic, 
        seen_ids: set
    ) -> List[Trend]:
        """Convert OpenAlex works to Trends"""
        trends = []
        
        for work in works:
            work_id = work.get('id', '')
            
            # Skip duplicates
            if work_id in seen_ids:
                continue
            
            # Quality filter: minimum citations
            citations = work.get('cited_by_count', 0)
            if citations < self.min_citations:
                continue
            
            seen_ids.add(work_id)
            
            # Parse publication date
            pub_date_str = work.get('publication_date')
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()
            
            # Build description
            description = self._build_description(work)
            
            # Determine category
            category = self._determine_category(work)
            
            # Get best URL (prefer DOI, fallback to OpenAlex)
            url = work.get('doi', work.get('id', ''))
            if url.startswith('https://openalex.org/'):
                # If no DOI, try to get landing page
                primary_loc = work.get('primary_location') or {}
                url = primary_loc.get('landing_page_url', url)
            
            # Get title
            title = work.get('title', 'Untitled')
            if not title or title == 'Untitled':
                title = work.get('display_name', 'Untitled')
            
            trends.append(Trend(
                title=title.strip(),
                description=description,
                url=url,
                source="OpenAlex",
                category=category,
                published_at=pub_date,
                topic_id=topic.id if topic else None,
                relevance_score=0.8,  # Citation-filtered works
                status="approved"
            ))
        
        return trends
    
    def _build_description(self, work: dict) -> str:
        """Build description with citations and metadata"""
        # Get abstract/description (OpenAlex has inverted_abstract)
        abstract = "No abstract available"
        inverted = work.get('abstract_inverted_index')
        if inverted:
            # Reconstruct abstract from inverted index (simplified)
            abstract = "Abstract available"  # Simplified for now
        
        # Get authors
        authorships = work.get('authorships', [])
        author_names = []
        for auth in authorships[:3]:
            author = auth.get('author') or {}
            name = author.get('display_name', '')
            if name:
                author_names.append(name)
        
        author_str = ", ".join(author_names)
        if len(authorships) > 3:
            author_str += f" +{len(authorships) - 3}"
        
        # Get metrics
        citations = work.get('cited_by_count', 0)
        year = work.get('publication_year', 'Unknown')
        
        # Get publication venue
        primary_loc = work.get('primary_location') or {}
        source = primary_loc.get('source') or {}
        venue = source.get('display_name', 'Unknown venue')
        
        # Check if open access
        is_oa = (work.get('open_access') or {}).get('is_oa', False)
        oa_badge = "🔓" if is_oa else "🔒"
        
        # Format: " Citations |  Authors |  Year |  Venue | OA Status"
        metrics = f"{oa_badge} {citations} citations |  {author_str} |  {year} |  {venue}"
        
        return metrics
    
    def _determine_category(self, work: dict) -> str:
        """Determine category based on concepts/topics"""
        concepts = work.get('concepts', [])
        
        if not concepts:
            return "research-paper"
        
        # Get top 3 concepts
        top_concepts = [c.get('display_name', '').lower() for c in concepts[:3]]
        
        # Map concepts to categories
        if any('artificial intelligence' in c or 'machine learning' in c for c in top_concepts):
            return "ai-paper"
        elif any('computer science' in c or 'programming' in c for c in top_concepts):
            return "cs-paper"
        elif any('biology' in c or 'medicine' in c or 'health' in c for c in top_concepts):
            return "bio-paper"
        elif any('physics' in c for c in top_concepts):
            return "physics-paper"
        elif any('chemistry' in c for c in top_concepts):
            return "chemistry-paper"
        elif any('mathematics' in c or 'statistics' in c for c in top_concepts):
            return "math-paper"
        else:
            return "research-paper"
