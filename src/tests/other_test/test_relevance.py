"""Test relevance scoring."""
from glint.utils.relevance import calculate_relevance, get_score_label, _is_exact_match
from glint.core.models import Trend, Topic
def test_relevance_scoring():
    """Test various relevance scenarios."""
    
    # Create a test topic
    topic = Topic(id=1, name="python", is_active=True)
    
    # Test 1: High relevance (exact match in title, from GitHub)
    trend1 = Trend(
        title="Python 3.13 Released",
        description="New features in Python",
        url="https://github.com/python/cpython",
        source="GitHub"
    )
    score1 = calculate_relevance(trend1, topic)
    assert score1 >= 0.7, f"Expected high score, got {score1}"
    print(f"✓ Test 1 passed: High relevance = {score1:.2f} {get_score_label(score1)}")
    
    # Test 2: Medium relevance (partial match, from Reddit)
    trend2 = Trend(
        title="Check out this Pythonic code style",
        description="Tutorial on writing clean code",
        url="https://reddit.com/r/programming",
        source="Reddit"
    )
    score2 = calculate_relevance(trend2, topic)
    assert 0.3 <= score2 < 0.7, f"Expected medium score, got {score2}"
    print(f"✓ Test 2 passed: Medium relevance = {score2:.2f} {get_score_label(score2)}")
    
    # Test 3: Low relevance (false positive - Monty Python)
    trend3 = Trend(
        title="Monty Python's Flying Circus",
        description="Classic comedy show",
        url="https://example.com",
        source="Reddit"
    )
    score3 = calculate_relevance(trend3, topic)
    assert score3 < 0.3, f"Expected low score, got {score3}"
    print(f"✓ Test 3 passed: False positive filtered = {score3:.2f} {get_score_label(score3)}")
    
    # Test 4: Source credibility matters
    trend_github = Trend(
        title="Python tools",
        description="Some tools",
        url="https://github.com",
        source="GitHub"
    )
    trend_devto = Trend(
        title="Python tools",
        description="Some tools",
        url="https://dev.to",
        source="Dev.to"
    )
    score_gh = calculate_relevance(trend_github, topic)
    score_dt = calculate_relevance(trend_devto, topic)
    assert score_gh > score_dt, "GitHub should score higher than Dev.to"
    print(f"✓ Test 4 passed: GitHub ({score_gh:.2f}) > Dev.to ({score_dt:.2f})")
    
    # Test 5: Exact match detection
    assert _is_exact_match("python", "learn python today") == True
    assert _is_exact_match("python", "pythonic code") == False
    print("✓ Test 5 passed: Exact match detection works")
    
    print("\n All tests passed!")
if __name__ == "__main__":
    test_relevance_scoring()
