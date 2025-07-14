# ── Base image ───────────────────────────────────────────────
FROM python:3.11-slim

# ── Env + working dir ────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app

# ── Install deps ─────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ──────────────────────────────────────────────
COPY . .

# ── Start gunicorn ───────────────────────────────────────────
# import path = app:app  (because /app/app.py exists)
CMD ["gunicorn", "--bind", ":8080", "app:app"]
