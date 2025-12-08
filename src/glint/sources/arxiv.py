"""ArXiv preprint fetcher for scientific papers."""

import re
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime, timedelta
from glint.core.models import Trend, Topic
from glint.sources.base import BaseFetcher
from glint.utils.cache import cached_fetch


class ArXivFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.days_back = 30  # Look back 30 days
        self.max_results = 20  # Results per topic
        self.base_url = "http://export.arxiv.org/api/query"
        
        # ArXiv category mappings for common topics
        self.category_map = {
            "ai": "cs.AI",
            "machine-learning": "cs.LG",
            "deep-learning": "cs.LG",
            "neural-networks": "cs.NE",
            "computer-vision": "cs.CV",
            "nlp": "cs.CL",
            "natural-language": "cs.CL",
            "robotics": "cs.RO",
            "crypto": "cs.CR",
            "algorithms": "cs.DS",
            "databases": "cs.DB",
            "quantum": "quant-ph",
            "physics": "physics",
            "math": "math",
            "statistics": "stat",
        }
    
    @cached_fetch(ttl=600)  # 10 minutes cache
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        trends = []
        seen_ids = set()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.days_back)
            
            if not topics:
                # No topics: fetch recent papers from popular CS categories
                papers = self._fetch_category("cs.AI", cutoff_date)
                trends.extend(self._process_papers(papers, None, seen_ids))
            else:
                # Fetch for each topic
                for topic in topics:
                    # Try to map topic to ArXiv category
                    category = self._get_arxiv_category(topic.name)
                    
                    if category:
                        # Category search (e.g., cs.AI)
                        papers = self._fetch_category(category, cutoff_date)
                    else:
                        # Keyword search in title/abstract
                        papers = self._fetch_keyword(topic.name, cutoff_date)
                    
                    trends.extend(self._process_papers(papers, topic, seen_ids))
                    
        except Exception as e:
            self.logger.error(f"Error fetching from ArXiv: {e}")
        
        return trends
    
    def _get_arxiv_category(self, topic_name: str) -> str:
        """Map topic name to ArXiv category if possible"""
        topic_lower = topic_name.lower().replace(" ", "-")
        return self.category_map.get(topic_lower)
    
    def _fetch_category(self, category: str, cutoff_date: datetime) -> List[dict]:
        """Fetch papers from a specific ArXiv category"""
        try:
            # Build query: category AND recent
            query = f"cat:{category}"
            
            params = {
                "search_query": query,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": self.max_results
            }
            
            response = self.http.get(self.base_url, params=params)
            
            if response.status_code == 200:
                return self._parse_atom_feed(response.content, cutoff_date)
            else:
                self.logger.warning(f"ArXiv API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error fetching ArXiv category {category}: {e}")
        
        return []
    
    def _fetch_keyword(self, keyword: str, cutoff_date: datetime) -> List[dict]:
        """Fetch papers matching keyword in title/abstract"""
        try:
            # Search in title and abstract
            query = f"all:{keyword}"
            
            params = {
                "search_query": query,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": self.max_results
            }
            
            response = self.http.get(self.base_url, params=params)
            
            if response.status_code == 200:
                return self._parse_atom_feed(response.content, cutoff_date)
                
        except Exception as e:
            self.logger.error(f"Error fetching ArXiv keyword {keyword}: {e}")
        
        return []
    
    def _parse_atom_feed(self, content: bytes, cutoff_date: datetime) -> List[dict]:
        """Parse ArXiv Atom XML feed"""
        papers = []
        
        try:
            root = ET.fromstring(content)
            
            # ArXiv uses Atom namespace
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            for entry in root.findall('atom:entry', ns):
                try:
                    # Extract paper data
                    paper = {
                        'id': entry.find('atom:id', ns).text if entry.find('atom:id', ns) is not None else "",
                        'title': entry.find('atom:title', ns).text if entry.find('atom:title', ns) is not None else "Untitled",
                        'summary': entry.find('atom:summary', ns).text if entry.find('atom:summary', ns) is not None else "",
                        'authors': [],
                        'published': None,
                        'pdf_url': "",
                        'categories': []
                    }
                    
                    # Extract authors
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            paper['authors'].append(name_elem.text)
                    
                    # Extract publication date
                    published_elem = entry.find('atom:published', ns)
                    if published_elem is not None:
                        paper['published'] = datetime.strptime(
                            published_elem.text[:10], "%Y-%m-%d"
                        )
                    
                    # Filter by date
                    if paper['published'] and paper['published'] < cutoff_date:
                        continue
                    
                    # Extract PDF link
                    for link in entry.findall('atom:link', ns):
                        if link.get('title') == 'pdf':
                            paper['pdf_url'] = link.get('href', '')
                            break
                    
                    # If no PDF link, use abstract URL
                    if not paper['pdf_url']:
                        paper['pdf_url'] = paper['id']
                    
                    # Extract categories
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            paper['categories'].append(term)
                    
                    papers.append(paper)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing ArXiv entry: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing ArXiv feed: {e}")
        
        return papers
    
    def _process_papers(
        self, 
        papers: List[dict], 
        topic: Topic, 
        seen_ids: set
    ) -> List[Trend]:
        """Convert ArXiv papers to Trends"""
        trends = []
        
        for paper in papers:
            arxiv_id = self._extract_arxiv_id(paper['id'])
            
            # Skip duplicates
            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)
            
            # Build description with authors and categories
            description = self._build_description(paper)
            
            # Determine category
            category = self._determine_category(paper)
            
            trends.append(Trend(
                title=paper['title'].strip(),
                description=description,
                url=paper['pdf_url'],
                source="ArXiv",
                category=category,
                published_at=paper['published'] or datetime.now(),
                topic_id=topic.id if topic else None,
                relevance_score=0.8,  # Scientific papers pre-filtered by ArXiv categories
                status="approved"  # All fetched papers are approved
            ))
        
        return trends
    
    def _extract_arxiv_id(self, url: str) -> str:
        """Extract ArXiv ID from URL"""
        # URL format: http://arxiv.org/abs/2312.12345v1
        match = re.search(r'(\d{4}\.\d{4,5})', url)
        return match.group(1) if match else url
    
    def _build_description(self, paper: dict) -> str:
        """Build description with authors and metadata"""
        authors = paper['authors'][:3]  # First 3 authors
        author_str = ", ".join(authors)
        if len(paper['authors']) > 3:
            author_str += f" +{len(paper['authors']) - 3} more"
        
        # Get primary category
        primary_cat = paper['categories'][0] if paper['categories'] else "Unknown"
        
        # Truncate abstract
        abstract = paper['summary'].replace('\n', ' ').strip()
        if len(abstract) > 200:
            abstract = abstract[:200] + "..."
        
        # Format: "Abstract | Authors | Category"
        return f"{abstract} | 👥 {author_str} | 📁 {primary_cat}"
    
    def _determine_category(self, paper: dict) -> str:
        """Determine category based on ArXiv categories"""
        if not paper['categories']:
            return "paper"
        
        primary = paper['categories'][0]
        
        # Map ArXiv categories to Glint categories
        if primary.startswith('cs.AI') or primary.startswith('cs.LG'):
            return "ai-paper"
        elif primary.startswith('cs.'):
            return "cs-paper"
        elif primary.startswith('physics'):
            return "physics-paper"
        elif primary.startswith('math'):
            return "math-paper"
        elif primary.startswith('stat'):
            return "stats-paper"
        else:
            return "paper"
