FROM python:3.9-slim

WORKDIR /app

# Copy requirements from agent_worker subdirectory
COPY agent_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files from agent_worker/src
COPY agent_worker/src/ ./src/
COPY agent_groq/ ./agent_groq

# Copy agent_core (if needed)
COPY agent_core/ ./agent_core/

# Set Python path to include all modules
ENV PYTHONPATH="/app:/app/agent_groq"

CMD ["python", "src/worker.py"]

