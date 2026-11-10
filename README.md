# Smart AI Gateway

A FastAPI application that routes prompts to OpenAI models using
keyword rules. It includes authentication, rate limiting, fallback
handling, response caching, and request logging.

## Features

- Simple prompts route to a lower-cost model.
- Selected keywords route to a stronger model.
- Eligible server errors trigger one backup model attempt.
- Matching responses are cached for five minutes.
- Callers can bypass caching with use_cache: false.
- Chat requests require a gateway access key.
- Up to five chat attempts are allowed per rolling 60 seconds.
- Responses include request IDs, timing, and token usage.
- Logs are written to logs/gateway.log.

## Setup

Requires Python 3.10 or newer.

Create and activate a virtual environment in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Copy .env.example to .env and replace the placeholder keys.
Never commit real keys.

## Run

```powershell
python -m uvicorn main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

Health check: http://127.0.0.1:8000/health

## Example request

In Swagger, enter GATEWAY_API_KEY's value in the x-api-key header.

```json
{
  "prompt": "Explain Python in one sentence.",
  "max_output_tokens": 100,
  "use_cache": true
}
```

## Tests

These tests use simulated results and do not call OpenAI:

```powershell
python test_fallback.py
python test_response_cache.py
```

## Files

- main.py: API endpoints, authentication, and model calls
- router.py: Keyword-based routing
- rate_limiter.py: Request frequency control
- response_cache.py: Temporary response storage
- test_fallback.py: Simulated fallback tests
- test_response_cache.py: Cache expiry tests
- requirements.txt: Installed dependencies
- .env.example: Configuration template

## Current limitations

This is a local development project. Cache and rate-limit state
are stored in memory, reset on restart, and are not shared between
server processes. The rate limit is shared across callers.
Routing uses keywords rather than an AI complexity classifier.