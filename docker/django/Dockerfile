FROM python:3.11-slim

# Working directory
WORKDIR /app

# Avoid pyc and buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies necessary for some Python packages
RUN apt-get update && apt-get install -y \
    gcc libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements/base.txt requirements/production.txt ./requirements/

# Install pip and Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements/production.txt

# Copy project
COPY . .

# Create static and media directories
RUN mkdir -p staticfiles media

#Execute collectstatic (ignore errors if run before migrations)
RUN python manage.py collectstatic --noinput || true

# Switch to a non-root user
USER 1000

# Gunicorn listens on port 8000
EXPOSE 8000

# command to run on container start
CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000"]
