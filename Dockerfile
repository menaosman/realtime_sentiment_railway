FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["sh", "-c", "gunicorn flask_dashboard:app --bind 0.0.0.0:${PORT:-5000}"]
