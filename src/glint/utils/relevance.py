""" Relevance scoring  utilities for trends filtering"""
import re
from glint.core.models import Trend, Topic

def calculate_relevance(trend: Trend, topic: Topic) -> float:
    """ Calculate how relevant a trend is to a topic
    Returns a score from 0.0 (irrelevant) to 1.0 (very relevant)
    scoring breakdown:
    - Topic match in title : up to 0.4
    - Topic match in description :  up to 0.3
    - Source credibility : up to 0.2
    - Engagement bonus: up to 0.1

    Args:
        trend: The trend to score
        topic: The topic to compare against
    Returns:
        float: The relevance score between 0.0 and 1.0
    """
    score = 0.0
    topic_lower = topic.name.lower()
    title_lower = trend.title.lower()
    description_lower = (trend.description or "").lower()

    #1. TITLE MATCHING (40% weight)
    if _is_exact_match(topic_lower, title_lower):
        score += 0.4
    elif topic_lower in title_lower:
        score += 0.2
    
    # 2. DESCRIPTION MATCHING (30% weight)
    if _is_exact_match(topic_lower, description_lower):
        score += 0.3
    elif topic_lower in description_lower:
        score += 0.15
    
    # 3. SOURCE CREDIBILITY (20% weight)
    source_weights = {
        'GitHub': 1.0,
        'Lobsters':0.95,
        'Hacker News': 0.8,
        'Reddit': 0.6,
        'Dev.to': 0.5,
        'Product Hunt':0.7
    }
    source_weight = source_weights.get(trend.source,0.5)
    score += source_weight * 0.2

    # 4. NEGATIVE KEYWORD (penalty for false positives)
    # these reduce the score if present
    negative_keywords = _get_negative_keywords(topic_lower)
    for keyword in negative_keywords:
        if keyword in title_lower or keyword in description_lower:
            score *= 0.5
            break
    
    # Cap at 1.0
    return min(score, 1.0)
#END calculate_relevance

def _is_exact_match(topic: str, text: str)-> bool:
    """ Check if the topic appears as a whole word in text.
    Examples:
        "python" matches "learn python"
        "python" does not match "pythonic"
    """
    #use word boundary regex
    pattern = rf'\b{re.escape(topic)}\b'
    return bool(re.search(pattern, text))
#END _is_exact_match

def _get_negative_keywords(topic: str)-> list[str]:
    """Get negative keywords for a topic
    These help filter out irrelevant results:
    - "python" -> exclude "monty python", "snake"

    """
    negative_map ={
        'python': ['monty', 'snake', 'reptile', 'circus'],
        'rust': ['game', 'corrosion', 'metal', 'oxide'],
        'go': ['game', 'chess', 'board'],  # "go" language vs "go" game
        'java': ['coffee', 'island'],
        'ruby': ['gem', 'stone', 'jewelry'],
        'swift': ['taylor', 'bird'],
        'dart': ['game', 'arrow'],
    }

    return negative_map.get(topic.lower(),[])
#END _get_negative_keywords

def get_score_label(score:float)->str:
    """Convert a score to a label"""
    if score >= 0.7:
        return "High"
    elif score >= 0.5:
        return "Medium"
    elif score >= 0.3:
        return "Low"
    else:
        return "Very Low"

