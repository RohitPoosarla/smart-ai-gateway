from unittest.mock import Mock, patch

import httpx
from openai import APIStatusError

from main import client, call_with_fallback, MODEL_MAP


# Simulate a server error from the first model.
fake_error = APIStatusError(
    "Simulated server failure",
    response=httpx.Response(
        status_code=500,
        request=httpx.Request(
            "POST",
            "https://api.openai.com/v1/responses",
        ),
    ),
    body={"error": {"message": "Simulated failure"}},
)

# Simulate a successful answer from the backup.
fake_response = Mock()
fake_response.output_text = "Hello from the backup model!"

with patch.object(
    client.responses,
    "create",
    side_effect=[fake_error, fake_response],
) as mock_create:
    response, model, fallback_used = call_with_fallback(
        prompt="Hello",
        route="cheap",
        max_tokens=100,
        request_id="fallback-test",
    )

    assert fallback_used is True
    assert model == MODEL_MAP["strong"]
    assert response is fake_response
    assert mock_create.call_count == 2

    print("PASS: Primary failed; backup returned an answer.")
    print("Backup model:", model)
    print("Fallback used:", fallback_used)

# Simulate an invalid OpenAI API key.
auth_error = APIStatusError(
    "Simulated authentication failure",
    response=httpx.Response(
        status_code=401,
        request=httpx.Request(
            "POST",
            "https://api.openai.com/v1/responses",
        ),
    ),
    body={"error": {"message": "Invalid API key"}},
)

with patch.object(
    client.responses,
    "create",
    side_effect=auth_error,
) as mock_create:
    try:
        call_with_fallback(
            prompt="Hello",
            route="cheap",
            max_tokens=100,
            request_id="auth-error-test",
        )
    except APIStatusError as error:
        assert error.status_code == 401
        assert mock_create.call_count == 1
        print("PASS: Authentication failure did not trigger fallback.")
    else:
        raise AssertionError("Expected an authentication error.")

# Simulate server errors from both models.
with patch.object(
    client.responses,
    "create",
    side_effect=[fake_error, fake_error],
) as mock_create:
    try:
        call_with_fallback(
            prompt="Hello",
            route="cheap",
            max_tokens=100,
            request_id="both-fail-test",
        )
    except APIStatusError as error:
        assert error.status_code == 500
        assert mock_create.call_count == 2

        print("PASS: Both models failed; stopped after two attempts.")
    else:
        raise AssertionError("Expected the backup error to be raised.")