import os
import socket

def create_tcp_sock(socket_host: str, socket_port: int):
    # Create an IPv4 (AF_INET) TCP (SOCK_STREAM) socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow instant reuse of the port after stopping the script
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind the socket to the address and port
    sock.bind((socket_host, socket_port))
    
    # Enable the server to accept connections
    sock.listen()
    print(f"Listening for connections on {socket_host}:{socket_port}...")

    return sock

def create_file_sock(socket_file):
    # Clean up the socket file if it already exists from a previous run
    if os.path.exists(socket_file):
        os.remove(socket_file)

    # Create a local Unix Domain Socket (AF_UNIX)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Bind the socket to the file path
    sock.bind(socket_file)
    
    # Enable the server to accept connections
    sock.listen()
    print(f"Listening for connections on file: {socket_file}...")

    return sock


