# Use Microsoft's official Playwright image
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Skip browser download at runtime (we'll use what's in the image)
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run Streamlit directly (no intermediate script)
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.headless=true"]
CMD ["--server.port=8501"]
