#!/usr/bin/env python3

"""
Multi-Ping ZMQ Test through SSL Proxy
Performs 5 pings with 1 second intervals, showing detailed logs for each
"""

import socket
import ssl
import json
import sys
import time

def test_zmq_ping_single(host="localhost", port=8443, ping_num=1):
    """Test single ZMQ ping through SSL proxy using raw TCP"""
    print(f"🔌 PING #{ping_num} - Testing ZMQ ping through SSL proxy at {host}:{port}", flush=True)
    
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
        print(f"  📡 Connecting to SSL proxy: {endpoint}", flush=True)
        ssl_socket.connect((host, port))
        
        print(f"  ✅ SSL connection established", flush=True)
        cipher_info = ssl_socket.cipher()
        print(f"  🔐 Cipher: {cipher_info}", flush=True)
        
        # Send ping command as raw JSON (no ZMQ framing)
        ping_request = {"command": "ping", "ping_id": ping_num, "timestamp": time.time()}
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
                server_time = response.get('timestamp')
                server_type = response.get('server_type', 'unknown')
                print(f"  ✅ PING #{ping_num} SUCCESS!", flush=True)
                print(f"  🕐 Server timestamp: {server_time}", flush=True)
                print(f"  🖥️  Server type: {server_type}", flush=True)
                ssl_socket.close()
                return True, response
            else:
                print(f"  ❌ Unexpected response: {response}", flush=True)
                ssl_socket.close()
                return False, response
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON response: {e}", flush=True)
            ssl_socket.close()
            return False, None
            
    except socket.timeout:
        print(f"  ❌ Timeout - no response from ZMQ server", flush=True)
        try:
            ssl_socket.close()
        except:
            pass
        return False, None
    except ConnectionRefusedError:
        print(f"  ❌ Connection refused - is SSL proxy running?", flush=True)
        return False, None
    except ssl.SSLError as e:
        print(f"  ❌ SSL Error: {e}", flush=True)
        return False, None
    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)
        try:
            ssl_socket.close()
        except:
            pass
        return False, None

def main():
    print("🧪 MULTI-PING ZMQ TEST (via SSL Proxy)", flush=True)
    print("=" * 60, flush=True)
    print("Testing: TCP Client → SSL → stunnel → ZMQ Server", flush=True)
    print("Performing 5 pings with 1 second intervals", flush=True)
    print("", flush=True)
    sys.stdout.flush()
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "localhost"
    
    # Track results
    successes = 0
    failures = 0
    responses = []
    
    # Run 5 pings with 1 second intervals
    for i in range(1, 6):
        print(f"┌─ PING {i}/5 " + "─" * 45, flush=True)
        
        success, response = test_zmq_ping_single(host, ping_num=i)
        
        if success:
            successes += 1
            responses.append(response)
            print(f"└─ ✅ PING {i} COMPLETED", flush=True)
        else:
            failures += 1
            print(f"└─ ❌ PING {i} FAILED", flush=True)
        
        print("", flush=True)
        
        # Wait 1 second before next ping (except after last ping)
        if i < 5:
            print(f"⏱️  Waiting 1 second before next ping...", flush=True)
            print("", flush=True)
            time.sleep(1)
    
    # Summary
    print("=" * 60, flush=True)
    print(f"🎯 MULTI-PING TEST SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Total Pings: 5", flush=True)
    print(f"✅ Successes: {successes}", flush=True)
    print(f"❌ Failures: {failures}", flush=True)
    print(f"📊 Success Rate: {(successes/5)*100:.1f}%", flush=True)
    
    if responses:
        print("", flush=True)
        print("📋 Response Details:", flush=True)
        for i, resp in enumerate(responses, 1):
            server_type = resp.get('server_type', 'unknown')
            timestamp = resp.get('timestamp', 'unknown')
            print(f"  Ping {i}: {server_type} @ {timestamp}", flush=True)
    
    print("", flush=True)
    if successes == 5:
        print("🎉 ALL PINGS SUCCESSFUL!", flush=True)
        print("   ✅ SSL proxy is stable", flush=True)
        print("   ✅ stunnel is forwarding reliably", flush=True)
        print("   ✅ ZMQ server is consistently responding", flush=True)
        print("   🔐 End-to-end SSL protection is working", flush=True)
        print("   📡 Raw TCP over SSL is performing well", flush=True)
        sys.exit(0)
    elif successes > 0:
        print(f"⚠️  PARTIAL SUCCESS ({successes}/5)", flush=True)
        print("   Some pings succeeded, check logs for failed attempts", flush=True)
        sys.exit(1)
    else:
        print("💥 ALL PINGS FAILED!", flush=True)
        print("   Debug steps:", flush=True)
        print("   1. Is SSL proxy running? (docker compose ps)", flush=True)
        print("   2. Check SSL proxy logs: (docker compose logs ssl-proxy)", flush=True)
        print("   3. Check ZMQ server logs: (docker compose logs zmq-server)", flush=True)
        print("   4. Try connectivity test: (make test)", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 