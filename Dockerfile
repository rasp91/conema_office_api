# Use Python as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libxml2 \
    libxslt1.1 \
    libjpeg-dev \
    zlib1g \
    fonts-liberation \
    fonts-dejavu \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and setuptools, then install dependencies without warnings
RUN python -m pip install --upgrade pip setuptools \
 && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# Copy the rest of the project into the container
COPY . .

# Make the startup script executable
RUN chmod +x docker-start.sh

# Default port (can be overridden by docker-compose)
ENV APP_PORT=80

# Expose the port the app runs on
EXPOSE $APP_PORT

# On startup: validate alembic migrations, apply if needed (logs → /app/logs/startup.log), then start uvicorn
CMD ["sh", "docker-start.sh"]
