FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#COPY . .          # ◆ copies app.py into /app, says file can not be found, neither does COPY app.py . or COPY backend/app.py . or COPY backend/ .
CMD ["gunicorn", "--bind", ":8080", "app:app"]
