# Gunicorn configuration file for Render deployment
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - adjust for Render's environment
# Use fewer workers to avoid memory issues and allow for longer timeouts
workers = min(multiprocessing.cpu_count(), 2)  # Max 2 workers for Render
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 100  # Lower max requests to prevent memory leaks
max_requests_jitter = 10

# Timeout settings - increased for Render environment
timeout = 120  # 2 minutes timeout
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "yt-music-api"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Render)
keyfile = None
certfile = None

# Additional settings for Render
preload_app = True
worker_tmp_dir = "/dev/shm"  # Use shared memory for temporary files 