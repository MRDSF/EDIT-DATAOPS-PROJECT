# Using Pydantic to Validate the API Payload

Pydantic is used here as a **gatekeeper** to validate the contract of the external API payload before accepting, storing, or processing the data.

## 1) Validation Flow

1. Receive the raw `data` from the API.
2. Run `ApiResponse.model_validate(data)`.
3. If it fails, handle the error.
4. If it passes, proceed with ingestion/storage.

This is a common and healthy pattern in data pipelines.

## 2) What Is Actually Being Validated

APIs like AlphaVantage return most numbers as strings (e.g. `"123.45"`).
Pydantic accepts these values and coerces them to `float`/`int` automatically.

In practice, this validates **convertibility**, which is usually what matters — not that the JSON already has native numeric types.

If you want to reject strings and only accept native types, use strict types (`StrictFloat`, `StrictInt`).
However, for AlphaVantage this would reject otherwise valid payloads.

## 3) High-Level Shape Validation (Recommended)

AlphaVantage may return error responses with keys like:

- `Note` (rate limit)
- `Error Message`
- `Information`

If you validate directly with the main schema, you'll get a `ValidationError`, but the message won't clearly indicate the business-level issue.

### Best Practice

Before calling `model_validate`, check for these error keys and raise a clear business error (e.g. rate limit hit, invalid symbol, API unavailable).

The recommended pipeline flow is:

1. High-level API error check.
2. Structural validation with Pydantic.
3. Persistence/processing.