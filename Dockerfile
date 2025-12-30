FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Tailwind CSS
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Install Tailwind CSS
RUN npm install -D tailwindcss @tailwindcss/forms @tailwindcss/typography
RUN npx tailwindcss init

# Expose port (Cloud Run uses 8080)
EXPOSE 8080

# Set port environment variable
ENV PORT=8080

# Use entrypoint script (runs migrations on startup)
ENTRYPOINT ["./docker-entrypoint.sh"]
