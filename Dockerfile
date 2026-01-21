# Use Microsoft's official Playwright image - has ALL dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x /app/start.sh

# Use the startup script
CMD ["/bin/bash", "/app/start.sh"]
