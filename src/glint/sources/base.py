"""Base fetcher class for all content sources."""

from abc import ABC, abstractmethod
from typing import List
from glint.core.models import Trend, Topic
from glint.core.logger import get_logger 
from glint.utils.http_client import http_client
from concurrent.futures import ThreadPoolExecutor, as_completed

class BaseFetcher(ABC):
    def __init__(self):
        self.http = http_client 
        self.max_workers = 5 # concurrent requests per fetcher
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        """Fetch trends for given topics."""
        pass
    #end fetch

    def fetch_all(self, topics: List[Topic]) -> List[Trend]:
        """Fetch trends in parallel for multiple topics"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            #submit all topic fetch tasks
            futures = {
                executor.submit(self._fetch_single_topic, topic): topic
                for topic in topics
            }

            all_trends = []
            #collect results as they complete
            for future in as_completed(futures):
                try:
                    trends = future.result(timeout=30) # TODO: make timeout configurable
                    all_trends.extend(trends)
                except Exception as ex:
                    topic = futures[future]
                    self.logger.error(f"Failed to fetch {topic.name}: {ex}")
            return all_trends
        #end fetch_all
    #end BaseFetcher

    def _fetch_single_topic(self,topic: Topic) -> List[Trend]:
        """
        Override in subclasses to fetch for a single topic.
        This enbales parallel fetching across topics
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _fetch_single_topic()"
        )
            
