FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestor.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the default command to run the ingester
ENTRYPOINT ["./entrypoint.sh"]
