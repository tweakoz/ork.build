#!/usr/bin/env python3

"""
Simple SSL ZMQ test client
Tests the SSL proxy -> ZMQ server connection with minimal dependencies
"""

import json
import ssl
import socket
import sys
import time

def test_ssl_connection(host="localhost", port=8443):
    """Test SSL connection to stunnel proxy"""
    print(f"🔌 Testing SSL connection to {host}:{port}")
    
    try:
        # Create SSL context (ignore cert verification for demo)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create and connect socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl_context.wrap_socket(sock, server_hostname=host)
        
        print(f"  Connecting...")
        ssl_sock.connect((host, port))
        print(f"  ✅ SSL connection established")
        print(f"  🔐 Cipher: {ssl_sock.cipher()}")
        
        # Test ZMQ-style JSON request
        request = {"command": "ping"}
        request_json = json.dumps(request)
        
        print(f"  📤 Sending: {request_json}")
        ssl_sock.send(request_json.encode('utf-8'))
        
        # Receive response
        response_data = ssl_sock.recv(1024)
        response_json = response_data.decode('utf-8')
        print(f"  📥 Received: {response_json}")
        
        # Parse response
        try:
            response = json.loads(response_json)
            if response.get('status') == 'success' and response.get('message') == 'pong':
                print(f"  ✅ ZMQ server responded correctly!")
                return True
            else:
                print(f"  ❌ Unexpected response: {response}")
                return False
        except json.JSONDecodeError:
            print(f"  ❌ Invalid JSON response")
            return False
            
    except ConnectionRefused:
        print(f"  ❌ Connection refused - is the SSL proxy running?")
        return False
    except socket.timeout:
        print(f"  ❌ Connection timeout")
        return False
    except ssl.SSLError as e:
        print(f"  ❌ SSL error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        try:
            ssl_sock.close()
        except:
            pass

def main():
    print("🧪 ZMQ SSL PROXY TEST")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    # Run the test
    success = test_ssl_connection(host)
    
    print("=" * 40)
    if success:
        print("🎉 TEST PASSED: SSL proxy is working!")
        print("   The unprotected ZMQ server is successfully")
        print("   wrapped with SSL encryption via stunnel")
        sys.exit(0)
    else:
        print("💥 TEST FAILED: SSL proxy is not working")
        print("   Check docker compose logs for details:")
        print("   docker compose logs ssl-proxy")
        print("   docker compose logs zmq-server")
        sys.exit(1)

if __name__ == "__main__":
    main() 