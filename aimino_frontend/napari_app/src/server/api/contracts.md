# Server API Contracts (stub)

## POST /invoke
- Request: `InvokeRequest`
```
{
  "user_input": "show nuclei layer",
  "context": [{"ts":"...","action":"layer_visibility",...}],
  "session_id": "<optional>"
}
```
- Response: `InvokeResponse`
```
{
  "final_commands": [{"action":"layer_visibility","name":"nuclei","op":"show"}],
  "session_id": "...",
  "latency_ms": 42
}
```
- Errors: `ErrorResponse`

## GET /healthz
- Response: `{ "status": "ok", "schema_version": "0.1" }`

## GET /session/{id} (future)
- Returns recent context/logs for a session.

