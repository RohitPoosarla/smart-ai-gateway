import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from secrets import compare_digest
from time import perf_counter
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from openai import APIStatusError, OpenAI, OpenAIError
from pydantic import BaseModel, Field

from rate_limiter import check_rate_limit
from response_cache import get_cached_response, save_cached_response
from router import choose_model


# Load settings from .env.
load_dotenv(Path(__file__).with_name(".env"))


# Configure terminal and file logging.
log_folder = Path(__file__).parent / "logs"
log_folder.mkdir(exist_ok=True)

logger = logging.getLogger("smart_ai_gateway")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_folder / "gateway.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# Configure OpenAI and FastAPI.
client = OpenAI(timeout=30.0, max_retries=0)

app = FastAPI(title="Smart AI Gateway")

MODEL_MAP = {
    "cheap": os.getenv("CHEAP_MODEL", "gpt-4.1-mini"),
    "strong": os.getenv("STRONG_MODEL", "gpt-4.1"),
}


# Call the selected model, with one eligible fallback attempt.
def call_with_fallback(prompt, route, max_tokens, request_id):
    primary_model = MODEL_MAP[route]
    backup_route = "strong" if route == "cheap" else "cheap"
    backup_model = MODEL_MAP[backup_route]

    try:
        response = client.responses.create(
            model=primary_model,
            input=prompt,
            max_output_tokens=max_tokens,
        )

        return response, primary_model, False

    except APIStatusError as error:
        # Only HTTP server errors qualify for fallback.
        if not 500 <= error.status_code < 600:
            raise

        # Stop when OpenAI explicitly asks us to wait.
        if error.response.headers.get("retry-after") is not None:
            raise

        # Avoid calling the same model twice.
        if backup_model == primary_model:
            raise

        logger.warning(
            "Trying fallback | request_id=%s | primary=%s | backup=%s",
            request_id,
            primary_model,
            backup_model,
        )

    response = client.responses.create(
        model=backup_model,
        input=prompt,
        max_output_tokens=max_tokens,
    )

    return response, backup_model, True


# Validate incoming request bodies.
class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    max_output_tokens: int = Field(default=500, ge=16, le=1000)
    use_cache: bool = True


@app.post("/v1/chat")
def chat(
    request: ChatRequest,
    x_api_key: str | None = Header(default=None),
):
    request_id = str(uuid4())

    # Check the gateway access key.
    expected_key = os.getenv("GATEWAY_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Gateway access key is not configured.",
        )

    if not x_api_key or not compare_digest(
        x_api_key.encode(),
        expected_key.encode(),
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid gateway access key.",
        )

    # Reject prompts containing only whitespace.
    prompt = request.prompt.strip()

    if not prompt:
        raise HTTPException(
            status_code=422,
            detail="Prompt cannot be blank.",
        )

    # Apply the gateway rate limit.
    check_rate_limit()

    # Choose the initial model.
    decision = choose_model(prompt)
    model_name = MODEL_MAP[decision["model"]]

    # Look for a matching cached response when enabled.
    cache_start = perf_counter()

    cache_key = (
        prompt,
        decision["model"],
        MODEL_MAP["cheap"],
        MODEL_MAP["strong"],
        request.max_output_tokens,
    )

    cached = (
        get_cached_response(cache_key)
        if request.use_cache
        else None
    )

    if cached is not None:
        cached["request_id"] = request_id
        cached["cache_hit"] = True
        cached["response_time_ms"] = round(
            (perf_counter() - cache_start) * 1000,
            2,
        )

        cached["original_usage"] = cached["usage"]
        cached["usage"] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

        logger.info(
            "Cache hit | request_id=%s | model=%s",
            request_id,
            cached["model"],
        )

        return cached

    # Call OpenAI when no cached response is used.
    try:
        start_time = perf_counter()

        logger.info(
            "Calling OpenAI | request_id=%s",
            request_id,
        )

        response, model_name, fallback_used = call_with_fallback(
            prompt=prompt,
            route=decision["model"],
            max_tokens=request.max_output_tokens,
            request_id=request_id,
        )

        response_time_ms = round(
            (perf_counter() - start_time) * 1000,
            2,
        )

    except OpenAIError as error:
        logger.error(
            "Chat failed | request_id=%s | selected_model=%s | error_type=%s",
            request_id,
            model_name,
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail={
                "request_id": request_id,
                "message": "OpenAI request failed.",
            },
        ) from None

    logger.info(
        "Chat completed | request_id=%s | route=%s | model=%s | time_ms=%s | total_tokens=%s",
        request_id,
        decision["model"],
        model_name,
        response_time_ms,
        response.usage.total_tokens if response.usage else None,
    )

    # Build the response.
    result = {
        "request_id": request_id,
        "route": decision["model"],
        "model": model_name,
        "fallback_used": fallback_used,
        "cache_hit": False,
        "reason": decision["reason"],
        "answer": response.output_text,
        "response_time_ms": response_time_ms,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response.usage else None,
    }

    # Save only completed answers when caching is enabled.
    if (
        request.use_cache
        and getattr(response, "status", None) == "completed"
        and response.output_text
    ):
        save_cached_response(cache_key, result)

    return result


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Smart AI Gateway",
    }