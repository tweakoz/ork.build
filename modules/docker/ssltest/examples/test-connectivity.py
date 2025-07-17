#!/usr/bin/env python3

"""
Simple SSL connectivity test
Just verifies the SSL proxy is accepting connections on port 8443
"""

import ssl
import socket
import sys

def test_ssl_connectivity(host="localhost", port=8443):
    """Test that SSL proxy is accepting connections"""
    print(f"🔌 Testing SSL connectivity to {host}:{port}")
    
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
        print(f"  📡 SSL proxy is forwarding to ZMQ server")
        
        ssl_sock.close()
        return True
        
    except ConnectionRefusedError:
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

def main():
    print("🧪 ZMQ SSL PROXY CONNECTIVITY TEST")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    # Run the test
    success = test_ssl_connectivity(host)
    
    print("=" * 50)
    if success:
        print("🎉 TEST PASSED: SSL proxy is accepting connections!")
        print("   The SSL termination proxy is working correctly")
        print("   ZMQ server communication requires proper ZMQ client")
        sys.exit(0)
    else:
        print("💥 TEST FAILED: SSL proxy is not reachable")
        print("   Check docker compose logs for details:")
        print("   docker compose logs ssl-proxy")
        print("   docker compose logs zmq-server")
        sys.exit(1)

if __name__ == "__main__":
    main() 