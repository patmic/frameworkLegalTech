# ══════════════════════════════════════════════════════════
#  MALTG Architecture Validator — Backend
#  UI UX Pro Max Skill — Glassmorphism Dashboard
# ══════════════════════════════════════════════════════════
FROM python:3.12-slim

WORKDIR /app

# Install system deps (Node.js for uipro-cli + Python for skill search engine)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uipro-cli globally (UI UX Pro Max skill)
RUN npm install -g uipro-cli

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
