FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY ollama_mcp_server.py .

# Non-root user for security
RUN useradd -m ollama && chown -R ollama:ollama /app
USER ollama

# Critical for stdio MCP transport — no buffering
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

# Default: stdio transport (Glama inspection compatible)
ENTRYPOINT ["python", "ollama_mcp_server.py"]
