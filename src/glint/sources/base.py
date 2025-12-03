"""Base fetcher class for all content sources."""

import requests
from abc import ABC, abstractmethod
from typing import List
from glint.core.models import Trend, Topic
from glint.core.logger import get_logger


class BaseFetcher(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, topics: List[Topic]) -> List[Trend]:
        pass
