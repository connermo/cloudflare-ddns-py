FROM python:3.9-slim

WORKDIR /app

# Install required dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create configuration directory
RUN mkdir -p /config

# Set configuration path
ENV CONFIG_PATH=/config/config.ini
ENV UPDATE_INTERVAL=300

# Run application
CMD ["python", "main.py"] 