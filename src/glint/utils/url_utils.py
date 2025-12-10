
"""URL utilities for deduplication and normalization"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def normalize_url(url: str) -> str:
    """
    Normalize a URL to help detect duplicates

    This function :
    1. Removes tracking parameters (utm_*, ref, source, etc)
    2. Standardizes to HTTPS
    3. Removes 'www.' subdomain 
    4. Removes trailing slashes
    5. Sorts remaining query parameters

    Args:
        url (str): The URL to normalize

    Returns:
        str: The normalized URL
    """ 
    if not url:
        return ""
    try:
        #parse the URL into components
        #urlparse returns: ParseResult(scheme, netloc, path, params, query, fragment)
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term','utm_content',
            'ref', 'source','campaign','fbclid','gclid','mc_cid','mc_eid',
            'si', 'igsh', 'yclid', '_hsenc', '_hsmi', 'hsCtaTracking'
        }
        clean_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }
        #sorted query parameters
        clean_query = urlencode(sorted(clean_params.items()), doseq=True) if clean_params else ""
    
        #Remove 'www. ' prefixe 
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
            
        # Remove standard ports
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            if port in ['80', '443']:
                netloc = host
        
        #remove trailing slash (unless it's the root path "/")
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'

        # rebuild the URL
        normalized = urlunparse((
            'https',    #always use HTTPS
            netloc,     # cleaned domain
            path,       #Path without trailing slash
            '',
            clean_query,
            ''   
        ))
        return normalized
    except Exception:
        #better to have duplicates than lose data
        return url

def urls_are_equivalent(url1: str, url2:str) -> bool:
    """
    check if two URLS point to the same content

    Args:
        url1: first URL
        url2: second URL
    Returns:
        True if URLS are equivalent after normalization

    """
    return normalize_url(url1) == normalize_url(url2)


