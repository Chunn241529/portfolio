FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose port
EXPOSE 8000

# Install specific model and prepare Ollama
RUN ollama serve & sleep 10 && \
    ollama pull gemma:4b && \
    pkill ollama

# Run Ollama in background and start the app
CMD ollama serve & sleep 10 && \
    uvicorn api:app --host 0.0.0.0 --port 8000
