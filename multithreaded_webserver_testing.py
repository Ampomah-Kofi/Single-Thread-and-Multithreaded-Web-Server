# Multithreaded Web Server with Request-Line Logging
# CS 538 Project 1 — Multithreaded Web Server (Port 7755)
# Author: Ampomah Kofi | CWID: 12504602
#
# This program builds on my single-threaded server. The difference here is
# that every new client connection runs inside its own thread. That way,
# the server can handle more than one browser request at a time.
# I tested it with small files (HTML, images, text) and a large media file,
# and the logs show the requests overlapping in real time.

from socket import *
from email.utils import formatdate
from urllib.parse import unquote
import threading
import mimetypes
import os

PORT = 7755
WEB_ROOT = os.getcwd()  # serve files from the folder where this script runs

# Turn a date into HTTP format (used in response headers)


def http_date():
    return formatdate(usegmt=True)

# Make sure the requested path doesn’t break out of the server folder


def safe_path(url_path: str) -> str:
    raw = unquote(url_path.split("?", 1)[0]).lstrip("/")
    if raw == "":
        raw = "webservertesting.html"   # default page when just "/" is requested
    safe = os.path.normpath(os.path.join(WEB_ROOT, raw))
    if not safe.startswith(WEB_ROOT):
        return None
    return safe

# This function is run in a separate thread for each client


def handle_client(client_socket, client_addr):
    print(
        f"Connected: {client_addr} (Thread: {threading.current_thread().name})")
    try:
        # Read the HTTP request
        request_data = client_socket.recv(4096).decode(errors="ignore")
        if not request_data:
            return

        lines = request_data.split("\r\n")
        request_line = lines[0]
        print("Request line:", request_line)

        # Look for User-Agent just to know which browser/tool connected
        for line in lines[1:]:
            if line.lower().startswith("user-agent:"):
                print("User-Agent:", line)
                break

        parts = request_line.split()
        if len(parts) != 3:
            send_error(client_socket, 400, "Bad Request")
            return

        method, path, version = parts

        # Only support GET in this simple server
        if method != "GET":
            send_error(client_socket, 405, "Method Not Allowed",
                       headers=["Allow: GET"])
            return

        # Map the URL to a real file path
        filepath = safe_path(path)
        if not filepath or not os.path.isfile(filepath):
            send_error(client_socket, 404, "Not Found")
            return

        # Guess the right MIME type so the browser knows how to show it
        content_type, _ = mimetypes.guess_type(filepath)
        if not content_type:
            content_type = "application/octet-stream"
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"

        # Read the file bytes
        with open(filepath, "rb") as f:
            content = f.read()

        # Build the HTTP response headers
        headers = [
            f"Date: {http_date()}",
            "Server: CS538Toy/1.0",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(content)}",
            "Connection: close",
        ]
        header_block = "HTTP/1.1 200 OK\r\n" + \
            "\r\n".join(headers) + "\r\n\r\n"

        # Send headers + file content
        client_socket.sendall(header_block.encode("iso-8859-1"))
        client_socket.sendall(content)

        print(f"200 OK -> {path} ({len(content)} bytes) "
              f"(Thread: {threading.current_thread().name})")

    except Exception as e:
        print("Error handling client:", e)
        try:
            send_error(client_socket, 500, "Internal Server Error")
        except:
            pass
    finally:
        client_socket.close()

# Send a basic error page back to the browser


def send_error(sock, code, reason, headers=None, body=None):
    if body is None:
        body = f"<html><body><h1>{code} {reason}</h1></body></html>".encode(
            "utf-8")
    base_headers = [
        f"Date: {http_date()}",
        "Server: CS538Toy/1.0",
        "Content-Type: text/html; charset=utf-8",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]
    if headers:
        base_headers.extend(headers)
    header_block = f"HTTP/1.1 {code} {reason}\r\n" + \
        "\r\n".join(base_headers) + "\r\n\r\n"
    sock.sendall(header_block.encode("iso-8859-1"))
    sock.sendall(body)
    print(f"{code} {reason}")

# keep listening for new connections


def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(("", PORT))
    server_socket.listen(5)
    print(f"Multithreaded server ready on port {PORT}...")

    while True:
        client_socket, client_addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_addr))
        client_thread.start()
        print("Ready to serve... (Accepted new connection)")


if __name__ == "__main__":
    main()
