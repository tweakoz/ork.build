#!/usr/bin/env python3

import zmq
import json
import time
import sys
import ssl
import socket

class SSLZMQClient:
    def __init__(self, host="localhost", ssl_port=8443, verify_cert=False):
        """
        Connect to ZMQ server through SSL proxy (stunnel)
        stunnel terminates SSL and forwards to ZMQ server
        """
        self.host = host
        self.ssl_port = ssl_port
        
        # Create SSL context
        if verify_cert:
            self.ssl_context = ssl.create_default_context()
        else:
            # For demo with self-signed certificates
            print("WARNING: SSL certificate verification is DISABLED")
            print("This is acceptable for demo purposes but NEVER in production!")
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # We'll create the SSL connection manually and use ZMQ over it
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Establish SSL connection to stunnel proxy"""
        try:
            # Create TCP socket
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Wrap with SSL
            self.socket = self.ssl_context.wrap_socket(
                raw_socket, 
                server_hostname=self.host if self.ssl_context.check_hostname else None
            )
            
            # Connect to stunnel
            print(f"Connecting to SSL proxy at {self.host}:{self.ssl_port}")
            self.socket.connect((self.host, self.ssl_port))
            
            print(f"SSL connection established")
            print(f"Cipher: {self.socket.cipher()}")
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_request(self, command, data=None):
        """Send a ZMQ-style request over SSL connection"""
        if not self.connected:
            raise Exception("Not connected")
        
        # Prepare request
        request = {"command": command}
        if data is not None:
            request["data"] = data
        
        request_str = json.dumps(request)
        print(f"Sending: {request_str}")
        
        # Send request (ZMQ format over SSL)
        message = request_str.encode('utf-8')
        self.socket.send(message)
        
        # Receive response
        response_bytes = self.socket.recv(4096)
        response_str = response_bytes.decode('utf-8')
        print(f"Received: {response_str}")
        
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": response_str}
    
    def test_commands(self):
        """Test various server commands"""
        print("\n=== Testing SSL ZMQ Connection ===\n")
        
        if not self.connect():
            print("Failed to establish SSL connection")
            return
        
        try:
            # Test ping
            print("1. Testing ping command:")
            response = self.send_request("ping")
            print(f"   Status: {response.get('status')}")
            print(f"   Message: {response.get('message')}")
            print()
            
            # Test echo
            print("2. Testing echo command:")
            test_data = "Hello from SSL client!"
            response = self.send_request("echo", test_data)
            print(f"   Status: {response.get('status')}")
            print(f"   Echo: {response.get('message')}")
            print()
            
            # Test info
            print("3. Testing info command:")
            response = self.send_request("info")
            print(f"   Status: {response.get('status')}")
            print(f"   Server: {response.get('server')}")
            print(f"   Version: {response.get('version')}")
            print()
            
            # Test unknown command
            print("4. Testing unknown command:")
            response = self.send_request("unknown")
            print(f"   Status: {response.get('status')}")
            print(f"   Message: {response.get('message')}")
            print(f"   Available: {response.get('available_commands')}")
            print()
            
        except Exception as e:
            print(f"Error during communication: {e}")
    
    def cleanup(self):
        print("Cleaning up SSL client...")
        if self.socket:
            self.socket.close()
        self.connected = False

def main():
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    client = SSLZMQClient(host=host, verify_cert=False)
    
    try:
        client.test_commands()
        print("=== SSL ZMQ Client Test Complete ===")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.cleanup()

if __name__ == "__main__":
    main() 