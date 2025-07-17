FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install pyzmq

# Create non-root user
RUN useradd -m -s /bin/bash zmquser

# Copy server code
COPY server.py /home/zmquser/
RUN chown zmquser:zmquser /home/zmquser/server.py
RUN chmod +x /home/zmquser/server.py

# Switch to non-root user
USER zmquser
WORKDIR /home/zmquser

# Expose ZMQ port (internal only)
EXPOSE 5555

# Run the server
CMD ["python", "server.py"] 