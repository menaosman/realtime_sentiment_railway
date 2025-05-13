# Use an official lightweight Python image
FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies needed for compiling Python packages
RUN apk add --no-cache build-base gcc musl-dev libffi-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8080

# Run the app with Gunicorn for production
CMD ["gunicorn", "flask_dashboard:app", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "4", "--timeout", "120"]
