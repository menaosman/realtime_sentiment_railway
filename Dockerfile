FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port expected by Railway
EXPOSE 8000

# Start the app using Gunicorn
CMD ["gunicorn", "flask_dashboard:app", "--bind", "0.0.0.0:${PORT}"]
