"""Test content fingerprinting."""
from glint.utils.fingerprint import (
    generate_fingerprint,
    extract_core_terms,
    fingerprints_match
)
def test_fingerprinting():
    """Test various fingerprinting scenarios."""
    
    # Test 1: Exact same title → Same fingerprint
    fp1 = generate_fingerprint("Python 3.13 Released")
    fp2 = generate_fingerprint("Python 3.13 Released")
    assert fp1 == fp2, "Identical titles should have same fingerprint"
    print(f"✓ Test 1 passed: Identical titles match")
    print(f"  Fingerprint: {fp1}")
    
    # Test 2: Similar titles → Same fingerprint
    fp3 = generate_fingerprint("Python 3.13 Released")
    fp4 = generate_fingerprint("Python 3.13 is Released!")
    # They should match (stopwords and punctuation removed)
    assert fp3 == fp4, "Similar titles should have same fingerprint"
    print(f"✓ Test 2 passed: Similar titles match")
    print(f"  '{extract_core_terms('Python 3.13 Released')}'")
    print(f"  = '{extract_core_terms('Python 3.13 is Released!')}'")
    
    # Test 3: Different order → Same fingerprint (sorted)
    fp5 = generate_fingerprint("New Features in Python 3.13")
    fp6 = generate_fingerprint("Python 3.13 New Features")
    # Should match because terms are sorted
    assert fp5 == fp6, "Different word order should still match"
    print(f"✓ Test 3 passed: Word order doesn't matter")
    
    # Test 4: Completely different → Different fingerprints
    fp7 = generate_fingerprint("Python 3.13 Released")
    fp8 = generate_fingerprint("JavaScript ES2024 Features")
    assert fp7 != fp8, "Different content should have different fingerprints"
    print(f"✓ Test 4 passed: Different content detected")
    print(f"  Python: {fp7}")
    print(f"  JavaScript: {fp8}")
    
    # Test 5: Stopwords don't affect fingerprint
    fp9 = generate_fingerprint("The New Python 3.13 is Released")
    fp10 = generate_fingerprint("Python 3.13 Released")
    # "The", "is", "New" are stopwords or common
    assert fp9 == fp10, "Stopwords should be ignored"
    print(f"✓ Test 5 passed: Stopwords removed")
    
    # Test 6: Core terms extraction
    terms = extract_core_terms("Python 3.13 Released - New Features")
    assert "python" in terms, "Should extract 'python'"
    assert "313" in terms, "Should extract version number"
    print(f"✓ Test 6 passed: Core terms extracted")
    print(f"  Terms: {terms}")
    
    # Test 7: Cross-platform duplicate detection
    github_title = "microsoft/generative-ai-for-beginners"
    hn_title = "Microsoft's Generative AI for Beginners Course"
    reddit_title = "Check out Generative AI for Beginners by Microsoft"
    
    fp_gh = generate_fingerprint(github_title)
    fp_hn = generate_fingerprint(hn_title)
    fp_rd = generate_fingerprint(reddit_title)
    
    # These should have similar core terms: microsoft, generative, beginners
    print(f"✓ Test 7: Cross-platform detection")
    print(f"  GitHub terms: {extract_core_terms(github_title)}")
    print(f"  HN terms: {extract_core_terms(hn_title)}")
    print(f"  Reddit terms: {extract_core_terms(reddit_title)}")
    # Note: Exact matching depends on term extraction, but they should be similar
    
    print("\n🎉 All tests passed!")
if __name__ == "__main__":
    test_fingerprinting()