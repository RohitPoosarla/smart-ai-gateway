from unittest.mock import patch

from response_cache import get_cached_response, save_cached_response


key = ("cache-expiry-test",)
data = {"answer": "Saved answer"}

# Simulate saving at time 100 seconds.
with patch("response_cache.monotonic", return_value=100):
    save_cached_response(key, data)

# One second later: the answer should still be available.
with patch("response_cache.monotonic", return_value=101):
    cached = get_cached_response(key)

    assert cached == data
    print("PASS: Saved answer is available before expiry.")

# After 301 seconds: the five-minute lifetime has expired.
with patch("response_cache.monotonic", return_value=401):
    cached = get_cached_response(key)

    assert cached is None
    print("PASS: Expired answer is removed.")