# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖项
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libfontconfig1 \
    libjpeg62-turbo \
    libpng-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    fontconfig \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# 💡 使用 gevent 以配合 Socket.IO 的并发需求
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent gevent-websocket

# Copy backend code
COPY . .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV STORAGE_PATH=/app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Run the application with gunicorn + gevent (Better for Socket.IO)
CMD ["gunicorn", "--worker-class", "gevent", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]
