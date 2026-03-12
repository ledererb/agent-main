FROM python:3.12-slim

# Create non-root user for production security
RUN useradd --create-home --shell /bin/bash agent

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r thinkai-voice-agent/requirements.txt

# Switch to non-root user
USER agent

WORKDIR /app/thinkai-voice-agent

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/api/health')" || exit 1

CMD ["bash", "start.sh", "start"]
