""" Content fingerprinting  for cross-platform deduplication    """

import re
import hashlib
from typing import Set

#common English stopwords that don't add much value to content fingerprinting
STOPWORDS: Set[str] = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 'had',
    'what', 'when', 'where', 'who', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'most', 'other', 'some', 'such', 'than', 'too',
    'very', 'can', 'just', 'should', 'now', 'i', 'you', 'your', 'we', 'our',
    'new', 'old', 'latest','recent'
}

# TODO: Add more stopwords for other languages

def generate_fingerprint(title: str, description: str= "") -> str:
    """
    Generate a content fingerprint based on title and description.

    This creates a hash that's the same dor similar content, even if the exact wording differs slightly.
    Algorithm:
    1. Normalize text (lowercase, remove punctuation)
    2. Remove stopwords (common words )
    3. Extract key terms (most meaningful words)
    4. Sort terms alphabetically (order doesn't matter)
    5. Hash the result 

    Args:
        title (str): The title of the content
        description (str, optional): The description of the content. Defaults to "".

    Returns:
        16-character fingerprint string
    """
    # combine title and description (title is more weight )
    text = title.lower()
    if description:
        text += " " + description[:100].lower()
    
    #step 1: Normalize text  
    #remove URLs
    text = re.sub(r'https?://\S+', '', text)
    #handle version numbers (join digits with dots)
    text = re.sub(r'(\d+)\.(\d+)', r'\1\2', text)

    #remove special characters and keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text) # à revoir
    #remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    #step 2: Split into words and remove stopwords
    words = text.split()
    meaningful_worlds = [word for word in words if word not in STOPWORDS and len(word) > 2]

    #step 3: Extract key terms (first 6 most meaningful words)
    key_terms = meaningful_worlds[:6]

    #step 4: Sort alphabetically (order doesn't matter)
    key_terms.sort()

    #step 5: Create fingerprint 
    if not key_terms:
        # use original text if no meaningful words 
        fingerprint_text = text[:50]
    else:
        fingerprint_text = " ".join(key_terms)
    
    #Hash using MD5 
    hash_object = hashlib.md5(fingerprint_text.encode())
    full_hash = hash_object.hexdigest()
    
    #return the first 16 characters of the hash
    return full_hash[:16]
#end generate_fingerprint

def extract_core_terms(title: str, max_terms: int =4) -> list:
    """
    Extract the core meaninguf terms from a title.

    Useful for debugging and understanding what the fingerprint is based on.

    Args:
        title: the title to analyze
        max_terms: the maximum number of terms to extract
    Returns:
        list of core terms
    """

    #Normalize 
    text = title.lower()
    #handle version numbers (join digits with dots)
    text = re.sub(r'(\d+)\.(\d+)', r'\1\2', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    #remove stopwords
    words = text.split()
    meaningful_words = [word for word in words if word not in STOPWORDS and len(word) > 2]
    
    #return top N, sorted
    return sorted(meaningful_words[:max_terms])

#end extract_core_terms

def fingerprints_match(fingerprint1: str, fingerprint2: str) -> bool:
    """
    Compare two fingerprints and return True if they exact match, False otherwise.
    """
    return fingerprint1 == fingerprint2
#end fingerprints_match


    
