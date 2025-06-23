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

# Expose the port the app runs on
EXPOSE 8005

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8005"]