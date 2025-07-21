FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app.py .          # ◆ copies app.py into /app
CMD ["gunicorn", "--bind", ":8080", "app:app"]
