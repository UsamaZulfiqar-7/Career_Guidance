# Python + OpenJDK standard container for reproducible Big Data & ML pipeline
FROM python:3.10-slim

# Install OpenJDK 17 LTS for PySpark compatibility and build essentials
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck for Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit dashboard by default
ENTRYPOINT ["streamlit", "run", "05_dashboard_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
