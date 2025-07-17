#!/usr/bin/env python3

"""
ZMQ Ping Test through SSL Proxy
Tests the complete chain: TCP Client → SSL → stunnel → ZMQ Server
Uses raw TCP instead of ZMQ protocol to work through stunnel
"""

import socket
import ssl
import json
import sys
import time

def test_zmq_ping(host="localhost", port=8443):
    """Test ZMQ ping through SSL proxy using raw TCP"""
    print(f"🔌 Testing ZMQ ping through SSL proxy at {host}:{port}", flush=True)
    
    try:
        # Create SSL context (ignore cert verification for demo)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create TCP socket and wrap with SSL
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.settimeout(5.0)  # 5 second timeout
        
        ssl_socket = ssl_context.wrap_socket(raw_socket, server_hostname=host)
        
        endpoint = f"{host}:{port}"
        print(f"  Connecting to SSL proxy: {endpoint}", flush=True)
        ssl_socket.connect((host, port))
        
        print(f"  ✅ SSL connection established", flush=True)
        print(f"  🔐 Cipher: {ssl_socket.cipher()}", flush=True)
        
        # Send ping command as raw JSON (no ZMQ framing)
        ping_request = {"command": "ping"}
        request_json = json.dumps(ping_request)
        print(f"  📤 Sending ping: {request_json}", flush=True)
        
        # Send as raw bytes
        ssl_socket.send(request_json.encode('utf-8'))
        print(f"  ⏳ Waiting for response (5 sec timeout)...", flush=True)
        
        # Receive response
        response_data = ssl_socket.recv(4096)
        response_json = response_data.decode('utf-8')
        print(f"  📥 Received: {response_json}", flush=True)
        
        # Parse and validate response
        try:
            response = json.loads(response_json)
            if response.get('status') == 'success' and response.get('message') == 'pong':
                print(f"  ✅ ZMQ ping successful!", flush=True)
                print(f"  🕐 Server timestamp: {response.get('timestamp')}", flush=True)
                ssl_socket.close()
                return True
            else:
                print(f"  ❌ Unexpected response: {response}", flush=True)
                ssl_socket.close()
                return False
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON response: {e}", flush=True)
            ssl_socket.close()
            return False
            
    except socket.timeout:
        print(f"  ❌ Timeout - no response from ZMQ server", flush=True)
        try:
            ssl_socket.close()
        except:
            pass
        return False
    except ConnectionRefusedError:
        print(f"  ❌ Connection refused - is SSL proxy running?", flush=True)
        return False
    except ssl.SSLError as e:
        print(f"  ❌ SSL Error: {e}", flush=True)
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)
        try:
            ssl_socket.close()
        except:
            pass
        return False

def main():
    print("🧪 ZMQ PING TEST (via SSL Proxy)", flush=True)
    print("=" * 50, flush=True)
    print("Testing: TCP Client → SSL → stunnel → ZMQ Server", flush=True)
    print("Using raw TCP instead of ZMQ protocol for stunnel compatibility", flush=True)
    print("", flush=True)
    sys.stdout.flush()
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    # Run the test
    success = test_zmq_ping(host)
    
    print("=" * 50, flush=True)
    if success:
        print("🎉 PING TEST PASSED!", flush=True)
        print("   ✅ SSL proxy is working", flush=True)
        print("   ✅ stunnel is forwarding correctly", flush=True)
        print("   ✅ ZMQ server is responding", flush=True)
        print("   🔐 End-to-end SSL protection is active", flush=True)
        print("   📡 Raw TCP over SSL works through stunnel", flush=True)
        sys.exit(0)
    else:
        print("💥 PING TEST FAILED!", flush=True)
        print("   Debug steps:", flush=True)
        print("   1. Is SSL proxy running? (docker compose ps)", flush=True)
        print("   2. Check SSL proxy logs: (docker compose logs ssl-proxy)", flush=True)
        print("   3. Check ZMQ server logs: (docker compose logs zmq-server)", flush=True)
        print("   4. Try connectivity test: (make test)", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 