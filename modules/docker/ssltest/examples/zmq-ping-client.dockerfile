FROM python:3.9-slim

# No additional packages needed - using built-in socket and ssl modules

# Copy test script
COPY test-zmq-ping.py /test-zmq-ping.py
RUN chmod +x /test-zmq-ping.py

# Run the test
CMD ["python", "/test-zmq-ping.py"] 