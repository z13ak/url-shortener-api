# url-shortener-api

A small REST API for shortening URLs, built with FastAPI and SQLite.

## Endpoints

| Method | Path            | Description                                      |
| ------ | --------------- | ------------------------------------------------- |
| POST   | `/shorten`      | Shorten a URL. Optional `custom_code`.             |
| GET    | `/{code}`       | 307-redirects to the original URL, counts a click. |
| GET    | `/stats/{code}` | Click count, original URL, and creation time.      |
| GET    | `/health`       | Liveness check.                                    |

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Interactive docs at `http://127.0.0.1:8000/docs`.

## Example

```bash
curl -X POST http://127.0.0.1:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://zleak.dev/some/long/path"}'
# -> {"code": "aZ3kQ1", "short_url": "/aZ3kQ1", "original_url": "https://zleak.dev/some/long/path"}

curl -i http://127.0.0.1:8000/aZ3kQ1
# -> HTTP/1.1 307 Temporary Redirect
# -> location: https://zleak.dev/some/long/path

curl http://127.0.0.1:8000/stats/aZ3kQ1
# -> {"code": "aZ3kQ1", "original_url": "...", "clicks": 1, "created_at": "..."}
```

Pass `custom_code` in the `/shorten` body to pick your own slug (3-30 chars,
letters/digits/`-`/`_`) instead of a random one - the API returns `409` if
it's already taken.
