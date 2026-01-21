# Use Microsoft's official Playwright image
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Skip browser download at runtime
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Use shell form so $PORT expands correctly
CMD /bin/bash -c "python -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true"
