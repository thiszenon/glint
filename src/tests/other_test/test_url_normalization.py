from glint.utils.url_utils import normalize_url, urls_are_equivalent

def test_normalization():
    """Test various URL normalization scenarios. """

    #Test 1: remove tracking parameters
    url1 = "https://example.com/article?utm_source=twitter&id=123"
    url2 = "https://example.com/article?id=123"

    assert normalize_url(url1) == normalize_url(url2), "should remove utm_source"
    print("Test 1 passed: Tracking parameters removed")

        # Test 2: Remove www
    url1 = "https://www.example.com/page"
    url2 = "https://example.com/page"
    assert normalize_url(url1) == normalize_url(url2), "Should remove www"
    print("✓ Test 2 passed: www removed")
    
    # Test 3: Remove trailing slash
    url1 = "https://example.com/article/"
    url2 = "https://example.com/article"
    assert normalize_url(url1) == normalize_url(url2), "Should remove trailing slash"
    print("✓ Test 3 passed: Trailing slash removed")
    
    # Test 4: Normalize to HTTPS
    url1 = "http://example.com/page"
    url2 = "https://example.com/page"
    assert normalize_url(url1) == normalize_url(url2), "Should normalize to HTTPS"
    print("✓ Test 4 passed: Normalized to HTTPS")

       # Test 5: Sort query parameters
    url1 = "https://example.com/page?b=2&a=1"
    url2 = "https://example.com/page?a=1&b=2"
    assert normalize_url(url1) == normalize_url(url2), "Should sort parameters"
    print("✓ Test 5 passed: Query parameters sorted")
    
    # Test 6: Real-world example
    url1 = "http://www.techcrunch.com/article/?utm_source=twitter&utm_campaign=spring"
    url2 = "https://techcrunch.com/article"
    assert urls_are_equivalent(url1, url2), "Should handle real-world URLs"
    print("✓ Test 6 passed: Real-world URLs matched")
    
    print("\n All tests passed!")
if __name__ == "__main__":
    test_normalization()
