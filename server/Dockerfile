FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install flask

# Copy server files
COPY server.py config.py hashcacher.py .

# Expose port
EXPOSE 5000

# Run the server
CMD ["python", "server.py"]