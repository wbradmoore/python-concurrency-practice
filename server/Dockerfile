FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install flask

# Copy server files
COPY demo_server.py config.py .

# Expose port
EXPOSE 5000

# Run the server
CMD ["python", "demo_server.py"]