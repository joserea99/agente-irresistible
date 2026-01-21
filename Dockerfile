# Use Microsoft's official Playwright image - has ALL dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies explicitly
RUN pip install --no-cache-dir -r requirements.txt

# Verify streamlit is installed
RUN python -m streamlit --version

# Copy application code
COPY . .

# Create a startup script for better debugging
RUN echo '#!/bin/bash\necho "Starting Streamlit on port $PORT"\npython -m streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false' > /app/start.sh && chmod +x /app/start.sh

# Use the startup script
CMD ["/bin/bash", "/app/start.sh"]
