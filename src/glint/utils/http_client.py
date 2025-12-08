
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

class HTTPClient:
    """singleton HTTP client with connection pooling"""
    _instance: Optional["HTTPClient"] =  None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    #end __new__

    def _initialize(self):
        self.session = requests.Session()
        #retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        #connection pool : 20 connections max
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        #set defaut timeout
        self.timeout = 30
    #end _initialize
    
    def get(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return self.session.get(url, **kwargs)
    #end get

#end HTTPClient
http_client = HTTPClient()