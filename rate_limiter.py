from collections import deque
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import HTTPException


request_times = deque()
rate_limit_lock = Lock()


def check_rate_limit():
    with rate_limit_lock:
        now = monotonic()

        while request_times and now - request_times[0] >= 60:
            request_times.popleft()

        if len(request_times) >= 5:
            retry_after = max(
                1,
                ceil(60 - (now - request_times[0])),
            )

            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many requests.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                },
            )

        request_times.append(now)