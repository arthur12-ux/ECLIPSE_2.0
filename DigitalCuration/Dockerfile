FROM python:3.11-slim

# Keep Python output unbuffered (helpful for logs)
ENV PYTHONUNBUFFERED=1

# Install minimal system packages required to build some Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the app
RUN useradd --create-home appuser
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application source
COPY . /app

# Switch to non-root user
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Default command: run the Streamlit search app in headless mode
CMD ["python", "-m", "streamlit", "run", "scripts/streamlit_search.py", "--server.port", "8501", "--server.headless", "true"]
