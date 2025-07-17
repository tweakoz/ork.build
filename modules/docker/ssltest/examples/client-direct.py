#!/usr/bin/env python3

import zmq
import json
import time
import sys

class DirectZMQClient:
    def __init__(self, host="localhost", port=5555):
        """
        Connect directly to ZMQ server (no SSL)
        This shows how the connection works without SSL proxy
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        
        endpoint = f"tcp://{host}:{port}"
        print(f"Connecting directly to ZMQ server at {endpoint}")
        self.socket.connect(endpoint)
    
    def send_request(self, command, data=None):
        """Send a request and return the response"""
        request = {"command": command}
        if data is not None:
            request["data"] = data
        
        request_str = json.dumps(request)
        print(f"Sending: {request_str}")
        
        # Send request
        self.socket.send_string(request_str)
        
        # Receive response
        response_str = self.socket.recv_string()
        print(f"Received: {response_str}")
        
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": response_str}
    
    def test_commands(self):
        """Test various server commands"""
        print("\n=== Testing Direct ZMQ Connection ===\n")
        
        # Test ping
        print("1. Testing ping command:")
        response = self.send_request("ping")
        print(f"   Status: {response.get('status')}")
        print(f"   Message: {response.get('message')}")
        print()
        
        # Test echo
        print("2. Testing echo command:")
        test_data = "Hello from direct client!"
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
    
    def cleanup(self):
        print("Cleaning up direct client...")
        self.socket.close()
        self.context.term()

def main():
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    # Note: This connects directly to port 5555 (ZMQ server)
    # In docker compose setup, this port is not exposed externally
    # so this client would need to run inside the docker network
    # or you'd need to expose port 5555 for testing
    client = DirectZMQClient(host=host, port=5555)
    
    try:
        client.test_commands()
        print("=== Direct ZMQ Client Test Complete ===")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Direct connection requires ZMQ server port 5555 to be accessible")
        print("Either run this inside docker network or expose port 5555 in docker compose")
    finally:
        client.cleanup()

if __name__ == "__main__":
    main() 