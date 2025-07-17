#!/usr/bin/env python3

"""
Hybrid ZMQ/TCP Server for SSL Proxy Demonstration
Handles both ZMQ protocol connections and raw TCP connections on the same port
"""

import zmq
import json
import time
import threading
import socket

def handle_tcp_client(client_socket, client_addr):
    """Handle raw TCP client (from stunnel)"""
    try:
        print(f"📡 Raw TCP client connected: {client_addr}", flush=True)
        
        # Receive raw data
        data = client_socket.recv(4096)
        if not data:
            print(f"  🔌 No data received from {client_addr}", flush=True)
            return
            
        request_json = data.decode('utf-8')
        print(f"  📥 Received raw TCP: {request_json}", flush=True)
        
        # Parse JSON request
        try:
            request = json.loads(request_json)
            command = request.get('command', '')
            
            # Handle commands (same logic as ZMQ server)
            if command == 'ping':
                response = {
                    'status': 'success',
                    'message': 'pong',
                    'timestamp': time.time(),
                    'server_type': 'hybrid_tcp'
                }
            elif command == 'echo':
                response = {
                    'status': 'success',
                    'message': request.get('message', ''),
                    'timestamp': time.time(),
                    'server_type': 'hybrid_tcp'
                }
            elif command == 'info':
                response = {
                    'status': 'success',
                    'server': 'Hybrid ZMQ/TCP Server',
                    'version': '1.0',
                    'protocols': ['zmq', 'tcp'],
                    'timestamp': time.time(),
                    'server_type': 'hybrid_tcp'
                }
            else:
                response = {
                    'status': 'error',
                    'message': f'Unknown command: {command}',
                    'server_type': 'hybrid_tcp'
                }
                
            # Send response as raw JSON
            response_json = json.dumps(response)
            client_socket.send(response_json.encode('utf-8'))
            print(f"  📤 Sent raw TCP response: {response_json}", flush=True)
            
        except json.JSONDecodeError as e:
            error_response = {
                'status': 'error', 
                'message': f'Invalid JSON: {e}',
                'server_type': 'hybrid_tcp'
            }
            response_json = json.dumps(error_response)
            client_socket.send(response_json.encode('utf-8'))
            print(f"  ❌ JSON decode error: {e}", flush=True)
            
    except Exception as e:
        print(f"  ❌ TCP client error: {e}", flush=True)
    finally:
        client_socket.close()
        print(f"  🔌 TCP client disconnected: {client_addr}", flush=True)

def tcp_server_thread():
    """Run TCP server for raw connections (from stunnel)"""
    # Create TCP server socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to same port as ZMQ (5555) - this will handle raw TCP 
    # ZMQ will handle ZMQ protocol on a different internal mechanism
    tcp_socket.bind(('0.0.0.0', 5556))  # Use different port for TCP
    tcp_socket.listen(5)
    
    print(f"🌐 TCP server listening on port 5556 (for stunnel/raw connections)", flush=True)
    
    while True:
        try:
            client_socket, client_addr = tcp_socket.accept()
            # Handle each client in a separate thread
            thread = threading.Thread(
                target=handle_tcp_client, 
                args=(client_socket, client_addr),
                daemon=True
            )
            thread.start()
        except Exception as e:
            print(f"❌ TCP server error: {e}", flush=True)

def zmq_server_thread():
    """Run ZMQ server for ZMQ protocol connections"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    
    print(f"⚡ ZMQ server listening on port 5555 (for ZMQ protocol)", flush=True)
    
    while True:
        try:
            # Wait for request
            message = socket.recv_string(zmq.NOBLOCK)
            print(f"📥 Received ZMQ: {message}", flush=True)
            
            # Parse JSON request
            try:
                request = json.loads(message)
                command = request.get('command', '')
                
                # Handle commands
                if command == 'ping':
                    response = {
                        'status': 'success',
                        'message': 'pong',
                        'timestamp': time.time(),
                        'server_type': 'hybrid_zmq'
                    }
                elif command == 'echo':
                    response = {
                        'status': 'success',
                        'message': request.get('message', ''),
                        'timestamp': time.time(),
                        'server_type': 'hybrid_zmq'
                    }
                elif command == 'info':
                    response = {
                        'status': 'success',
                        'server': 'Hybrid ZMQ/TCP Server',
                        'version': '1.0',
                        'protocols': ['zmq', 'tcp'],
                        'timestamp': time.time(),
                        'server_type': 'hybrid_zmq'
                    }
                else:
                    response = {
                        'status': 'error',
                        'message': f'Unknown command: {command}',
                        'server_type': 'hybrid_zmq'
                    }
                    
            except json.JSONDecodeError as e:
                response = {
                    'status': 'error', 
                    'message': f'Invalid JSON: {e}',
                    'server_type': 'hybrid_zmq'
                }
            
            # Send response
            response_json = json.dumps(response)
            socket.send_string(response_json)
            print(f"📤 Sent ZMQ response: {response_json}", flush=True)
            
        except zmq.Again:
            # No message available, continue
            time.sleep(0.01)
        except Exception as e:
            print(f"❌ ZMQ server error: {e}", flush=True)
            break
    
    context.term()

def main():
    print("🚀 Starting Hybrid ZMQ/TCP Server", flush=True)
    print("=" * 50, flush=True)
    print("  ⚡ ZMQ Protocol: port 5555", flush=True)
    print("  🌐 TCP Protocol: port 5556", flush=True) 
    print("  🔐 SSL Proxy Target: tcp://zmq-server:5556", flush=True)
    print("=" * 50, flush=True)
    
    # Start TCP server in background thread
    tcp_thread = threading.Thread(target=tcp_server_thread, daemon=True)
    tcp_thread.start()
    
    # Start ZMQ server in background thread  
    zmq_thread = threading.Thread(target=zmq_server_thread, daemon=True)
    zmq_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down hybrid server", flush=True)

if __name__ == "__main__":
    main() 