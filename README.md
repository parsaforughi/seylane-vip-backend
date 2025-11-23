# Telegram VIP Passport Backend

```bash
$ cd backend
$ cp .env.example .env
# fill DATABASE_URL, REDIS_URL, and TELEGRAM_BOT_TOKEN
$ poetry install
$ poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI app exposes a `/health` endpoint for simple availability checks.
