FROM python:3.12-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements/base.txt /app/requirements/
COPY requirements/prod.txt /app/requirements/
RUN pip install --upgrade pip && \
    pip install -r requirements/prod.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD gunicorn healthcare_project.wsgi:application --bind 0.0.0.0:8000