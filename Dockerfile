# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


RUN mkdir -p /app/podcasts /app/reports

# Copy app code
COPY . .

# Expose ports
EXPOSE 8000


# Run both FastAPI and Streamlit using subprocess
CMD ["sh", "-c", "uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 & streamlit run src/frontend/app.py --server.port 8501 --server.address 0.0.0.0"]
