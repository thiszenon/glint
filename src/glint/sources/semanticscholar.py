"""Semantic Scholar fetcher for CS research papers with citations."""

import re
from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic

from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class SemanticScholarFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Look back 30 days
        self.max_results = 20  # Results per topic
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.min_citations = 5  # Minimum citations for quality
    
    @cached_fetch(ttl=600)  # 10 minutes cache
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_ids = set()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.days_back)
            year_filter = cutoff_date.year
            
            if not topics:
                # No topics: fetch recent influential CS papers
                papers = self._search_papers("computer science", year_filter)
                trends.extend(self._process_papers(papers, None, seen_ids))
            else:
                # Fetch for each topic
                for topic in topics:
                    papers = self._search_papers(topic.name, year_filter)
                    trends.extend(self._process_papers(papers, topic, seen_ids))
                    
        except Exception as e:
            self.logger.error(f"Error fetching from Semantic Scholar: {e}")
        
        return trends
    
    def _search_papers(self, query: str, year: int) -> List[dict]:
        """Search for papers using S2 API"""
        try:
            # API endpoint
            url = f"{self.base_url}/paper/search"
            
            params = {
                "query": query,
                "year": f"{year}-",  # Papers from year onwards  
                "limit": self.max_results,
                "fields": "paperId,title,abstract,year,citationCount,influentialCitationCount,authors,publicationDate,url,fieldsOfStudy"
            }
            
            response = self.http.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            elif response.status_code == 429:
                self.logger.warning("Semantic Scholar rate limit hit")
            else:
                self.logger.warning(f"Semantic Scholar API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error searching Semantic Scholar: {e}")
        
        return []
    
    def _process_papers(
        self, 
        papers: List[dict], 
        topic: Topic, 
        seen_ids: set
    ) -> List[Trend]:
        """Convert S2 papers to Trends"""
        trends = []
        
        for paper in papers:
            paper_id = paper.get('paperId', '')
            
            # Skip duplicates
            if paper_id in seen_ids:
                continue
            
            # Quality filter: minimum citations
            citations = paper.get('citationCount', 0)
            if citations < self.min_citations:
                continue
            
            seen_ids.add(paper_id)
            
            # Parse publication date
            pub_date_str = paper.get('publicationDate')
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                except:
                    pub_date = datetime.now()
            else:
                # Fallback to year
                year = paper.get('year')
                pub_date = datetime(year, 1, 1) if year else datetime.now()
            
            # Build description
            description = self._build_description(paper)
            
            # Determine category
            category = self._determine_category(paper)
            
            # Get URL (prefer S2 URL, fallback to DOI/arxiv)
            url = paper.get('url', f"https://www.semanticscholar.org/paper/{paper_id}")
            
            trends.append(Trend(
                title=paper.get('title', 'Untitled').strip(),
                description=description,
                url=url,
                source="Semantic Scholar",
                category=category,
                published_at=pub_date,
                topic_id=topic.id if topic else None,
                relevance_score=0.8,  # Citation-filtered papers
                status="approved"
            ))
        
        return trends
    
    def _build_description(self, paper: dict) -> str:
        """Build description with citations and authors"""
        # Get abstract
        abstract = paper.get('abstract', 'No abstract available')
        if abstract and len(abstract) > 200:
            abstract = abstract[:200] + "..."
        
        # Get authors
        authors = paper.get('authors', [])
        author_names = [a.get('name', '') for a in authors[:3]]
        author_str = ", ".join(author_names)
        if len(authors) > 3:
            author_str += f" +{len(authors) - 3}"
        
        # Get metrics
        citations = paper.get('citationCount', 0)
        influential = paper.get('influentialCitationCount', 0)
        year = paper.get('year', 'Unknown')
        
        # Format: "Abstract | 📊 Citations | 🌟 Influential | 👥 Authors | 📅 Year"
        metrics = f"📊 {citations} citations"
        if influential > 0:
            metrics += f" | 🌟 {influential} influential"
        metrics += f" | 👥 {author_str} | 📅 {year}"
        
        return f"{abstract} | {metrics}"
    
    def _determine_category(self, paper: dict) -> str:
        """Determine category based on fields of study"""
        fields = paper.get('fieldsOfStudy', [])
        
        if not fields:
            return "cs-paper"
        
        fields_lower = [f.lower() for f in fields]
        
        # Map fields to categories
        if any(f in fields_lower for f in ['machine learning', 'artificial intelligence', 'deep learning', 'neural network']):
            return "ai-paper"
        elif any(f in fields_lower for f in ['computer vision', 'image processing']):
            return "vision-paper"
        elif any(f in fields_lower for f in ['natural language processing', 'computational linguistics']):
            return "nlp-paper"
        elif any(f in fields_lower for f in ['computer science']):
            return "cs-paper"
        elif any(f in fields_lower for f in ['biology', 'medicine', 'bioinformatics']):
            return "bio-paper"
        else:
            return "research-paper"
