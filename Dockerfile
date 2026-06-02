FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files first
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv sync --frozen || uv sync

# Copy project files
COPY . .

# Expose backend and frontend ports
EXPOSE 8000
EXPOSE 8501

# Make startup script executable
RUN chmod +x run_astra.sh

# Start full app
CMD ["./run_astra.sh"]
