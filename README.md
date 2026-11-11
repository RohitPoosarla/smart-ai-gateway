## Smart AI Gateway

A Python project that chooses between two AI models, returns an
answer, and tracks how each request was handled.

## Why I built it

- To learn how applications connect to AI models.
- To route simple and complex questions to different models.
- To practice handling failures, controlling usage, and reusing answers.

## What it does

- **Model selection:** Uses keywords to choose a model.
  - Simple prompts use the `cheap` route.
  - Keywords such as `debug` and `architecture` use the `strong` route.
- **Backup model:** Tries another model once after certain server errors.
- **Saved answers:** Reuses matching answers for up to five minutes.
- **Fresh answers:** Lets the caller skip saved answers.
- **Access key:** Requires a gateway key before accepting chat requests.
- **Usage limit:** Allows five chat attempts within a rolling 60 seconds.
- **Request tracking:** Gives each accepted chat request a unique ID.
- **Monitoring:** Shows response time and token usage.
- **Logs:** Records request details in the terminal and a local file.

## How a request works

1. The user sends a question and gateway access key.
2. The gateway checks the input, key, and request limit.
3. Keyword rules choose the model route.
4. If a matching saved answer exists and caching is enabled, it is returned.
5. Otherwise, the gateway calls OpenAI.
6. If an eligible server error occurs, it tries the backup model once.
7. The gateway returns the answer and request details.

## Tools used

- Python
- FastAPI
- OpenAI API
- Pydantic
- Git and GitHub
- Python logging and testing tools

## Run the project locally

- Install Python 3.10 or newer.
- Clone the project:

```powershell
git clone https://github.com/RohitPoosarla/smart-ai-gateway.git
cd smart-ai-gateway
```

- Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Install the required packages:

```powershell
python -m pip install -r requirements.txt
```

- Copy `.env.example` to `.env` for a new checkout.
- Replace the placeholders with your own keys.
- Use separate keys for OpenAI and gateway access.
- Keep real keys private.

- Start the server:

```powershell
python -m uvicorn main:app --reload
```

- Open Swagger: http://127.0.0.1:8000/docs
- Enter your gateway key in the `x-api-key` field.
- Send a request using the example below.

## Example request

```json
{
  "prompt": "Explain Python in one sentence.",
  "max_output_tokens": 100,
  "use_cache": true
}
```

- `prompt`: The question to send.
- `max_output_tokens`: The maximum output length in tokens.
- `use_cache`: Whether the gateway can reuse a saved answer.

## Understanding the response

- `request_id`: Helps find the matching log entry.
- `route`: The route originally selected by the keyword rules.
- `model`: The model that generated the answer.
- `fallback_used`: Whether the backup model generated it.
- `cache_hit`: Whether the answer came from saved results.
- `response_time_ms`: Time measured for the model call or cache path.
- `usage`: Tokens used by this request.
- `original_usage`: On cache hits, tokens used to generate the saved answer.

## What I tested

- Empty, missing, spaces-only, and oversized prompts are rejected.
- A missing gateway key is rejected.
- A correct gateway key allows a valid request.
- Simple and keyword-matched prompts select the expected routes.
- Too many requests return a wait time.
- Repeated requests can use saved answers.
- Cache bypass makes a new model call.
- Simulated server failures trigger the backup model.
- Simulated authentication failures do not trigger fallback.
- If both models fail, calls stop after two attempts.
- Saved answers expire after five minutes.

## Run the automated tests

```powershell
python test_fallback.py
python test_response_cache.py
```

- These tests use simulated results.
- They do not make paid OpenAI calls.

## Current limitations

- The project currently runs locally.
- Model selection uses keywords, not an AI assessment of difficulty.
- Saved answers and request counts reset when the server restarts.
- The request limit is shared across callers.
- Fallback does not cover every type of failure.
- Token counts show successful generation usage, not a complete billing report.

## Future improvements

- Add a Streamlit interface.
- Improve error messages.
- Add more automated tests.
- Support multiple users and server processes.