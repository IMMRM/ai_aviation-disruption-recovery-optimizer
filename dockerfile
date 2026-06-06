# ============================================================
# Base Image
# ============================================================

FROM python:3.12-slim

# ============================================================
# Environment Variables
# ============================================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ============================================================
# System Dependencies
# ============================================================

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Working Directory
# ============================================================

WORKDIR /app

# ============================================================
# Install Python Dependencies
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Copy Project Files
# ============================================================

COPY . .

# ============================================================
# Streamlit Configuration
# ============================================================

RUN mkdir -p /root/.streamlit

RUN echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
port = 8501\n\
" > /root/.streamlit/config.toml

# ============================================================
# Expose Streamlit Port
# ============================================================

EXPOSE 8501

# ============================================================
# Health Check
# ============================================================

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ============================================================
# Start Application
# ============================================================

CMD ["streamlit", "run", "streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]