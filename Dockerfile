# TODO: Use python:3.10-slim as base image
FROM python:3.10-slim

# TODO: Set working directory
WORKDIR /app

# TODO: Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# TODO: Copy app.py
COPY app.py .

EXPOSE 5000

# TODO: Command to run the app
# This is essentially what docker runs when a container starts from this image
CMD ["python3", "app.py"]