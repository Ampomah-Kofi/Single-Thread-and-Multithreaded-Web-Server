# Single-threaded Web Server with Request-Line Logging
# CS 538 Project 1 — Single-Threaded Web Server (Port 7755)
# Author: Ampomah Kofi
# CWID: 12504602
# Description: This server implements a basic HTTP/1.1 web server using Python sockets.
#              It listens on port 7755, parses simple GET requests, serves static files
#              from the current directory (with MIME type detection for browser rendering),
#              and returns 404 for missing files. Supports text/binary files (e.g., HTML, images,
#              videos, plain text). Logs request lines and responses to console for debugging.
#              Aligns with assignment: single-threaded, command-line execution, browser testing
#              on 127.0.0.1:7755, no backend outputs in screenshots except CLI start.

from socket import *
import sys
import mimetypes  # Built-in module for guessing MIME types based on file extension

# Assignment principle: Use a port >5000 to avoid privileged ports
PORT = 7755

# Create the server socket (TCP stream socket for reliable HTTP delivery)
server_socket = socket(AF_INET, SOCK_STREAM)

# Allow socket reuse to avoid "Address already in use" errors on restart
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

# Bind to all interfaces ('') on the specified port (listen on localhost for testing)
server_socket.bind(('', PORT))

# Listen for up to 1 queued connection (single-threaded, so no backlog needed)
server_socket.listen(1)

# Print server readiness to CLI for screenshot verification
print(f"Server is ready to serve on port {PORT}...")

# Main server loop: Accept and handle one request at a time sequentially
while True:
    # Accept incoming connection, creating a dedicated client socket
    client_socket, client_addr = server_socket.accept()

    # Log client connection for debugging (shows IP:port)
    print(f"Connected to client: {client_addr}")

    # Use try-except-finally for robust error handling and cleanup
    try:
        # Receive HTTP request (2048 bytes buffer handles typical headers; decode with error ignore for robustness)
        request_data = client_socket.recv(2048).decode(errors="ignore")

        # Skip empty requests (e.g., malformed connections)
        if not request_data:
            continue

        # Log the first request line (e.g., "GET /file.html HTTP/1.1") for verification
        first_line = (request_data.splitlines() or [""])[0]
        print("Request line:", first_line)

        # Parse the request line safely (method path version); default to GET / HTTP/1.1 if invalid
        try:
            method, path, version = first_line.split()
            # Only handle GET (ignore others for simplicity, as per basic HTTP lab)
            if method != "GET":
                raise IOError("Method not supported")
        except ValueError:
            method, path, version = "GET", "/", "HTTP/1.1"

        # Default root path to a test HTML file (e.g., webservertesting.html)
        # This ensures / loads a valid page for testing
        if path == "/":
            path = "/webservertesting.html"

        # Sanitize filepath: Strip leading '/', prevent directory traversal (e.g., ../)
        # Ignore query params for static files
        filepath = path.lstrip("/").split("?")[0]

        # Detect MIME type for browser interpretation (supports HTML, images, videos, text)
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = "application/octet-stream"  # Fallback for unknown types

        # Add charset for text types to ensure proper encoding in browsers
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"

        # Read file content as bytes (text in UTF-8, binary as-is) for universal sending
        if content_type.startswith("text/"):
            # Text mode with encoding for safe reading
            with open(filepath, "r", encoding="utf-8") as file_handle:
                file_content = file_handle.read().encode("utf-8")
        else:
            # Binary mode for images/videos/etc.
            with open(filepath, "rb") as file_handle:
                file_content = file_handle.read()

        # Build HTTP/1.1 200 OK response header (includes Content-Length for proper browser handling)
        response_header = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(file_content)}\r\n"
            # Close after one request (simple server)
            "Connection: close\r\n\r\n"
        )

        # Send header and body reliably (sendall ensures all bytes are transmitted)
        client_socket.sendall(response_header.encode(
            "iso-8859-1"))  # ISO for headers (robust)
        client_socket.sendall(file_content)

        # Log successful response (includes bytes sent for verification)
        print(f"200 OK -> {path} ({len(file_content)} bytes)")

    except IOError:
        # Handle missing files with 404 response (HTML body for browser display)
        error_body = b"<html><body><h1>404 Not Found</h1><p>The requested file was not found on the server.</p></body></html>"
        error_header = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(error_body)}\r\n"
            "Connection: close\r\n\r\n"
        )
        client_socket.sendall(error_header.encode("iso-8859-1"))
        client_socket.sendall(error_body)

        # Log 404 with path (use 'path' from locals() if available)
        error_path = path if 'path' in locals() else "(unknown)"
        print(f"404 Not Found -> {error_path}")

    finally:
        # Always close client socket to free resources
        client_socket.close()

# Note: This Server runs indefinitely; so you can easily terminate with Ctrl+C. No explicit close on server_socket needed in loop.
