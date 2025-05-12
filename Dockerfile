FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Use environment variable if set, otherwise default to 8000
CMD ["sh", "-c", "gunicorn flask_dashboard:app --bind 0.0.0.0:${PORT:8000}"]
