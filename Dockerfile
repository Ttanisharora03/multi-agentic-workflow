FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if any are needed (e.g. for building packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first to leverage Docker cache
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir .[db,tools]

# Copy application source code and frontend
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
