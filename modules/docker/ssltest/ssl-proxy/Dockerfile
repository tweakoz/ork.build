FROM debian:bullseye-slim

# Install stunnel and openssl
RUN apt-get update && apt-get install -y \
    stunnel4 \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Create stunnel user and group (if they don't exist)
RUN groupadd -f stunnel && \
    useradd -g stunnel -s /bin/false stunnel

# Create necessary directories
RUN mkdir -p /var/run /var/log /etc/stunnel

# Copy configuration and certificate generation script
COPY stunnel.conf /etc/stunnel/stunnel.conf
COPY generate-certs.sh /usr/local/bin/generate-certs.sh
RUN chmod +x /usr/local/bin/generate-certs.sh

# Generate certificates at build time
RUN /usr/local/bin/generate-certs.sh

# Create startup script  
RUN echo '#!/bin/bash' > /usr/local/bin/start-stunnel.sh && \
    echo 'echo "Starting stunnel SSL proxy..."' >> /usr/local/bin/start-stunnel.sh && \
    echo 'echo "Forwarding SSL port 8443 -> zmq-server:5555"' >> /usr/local/bin/start-stunnel.sh && \
    echo 'exec stunnel /etc/stunnel/stunnel.conf' >> /usr/local/bin/start-stunnel.sh && \
    chmod +x /usr/local/bin/start-stunnel.sh

# Expose SSL port
EXPOSE 8443

# Run stunnel
CMD ["/usr/local/bin/start-stunnel.sh"] 