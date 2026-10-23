# Test suite fixture with documented mock dummy token
# This is an intended DECOY (false positive) for testing AI triage.
# Local Gemma 4 should recognize this as a test mock and down-rank it.

MOCK_TEST_SECRET = "sk-test-dummy-mock-secret-key-for-unit-testing-only-12345678"  # DECOY-KEY

def test_placeholder():
    assert len(MOCK_TEST_SECRET) > 10
