import socket
import os
import threading
import time
from email.utils import formatdate

HOST = '127.0.0.1'
PORT = 8889
WEB_ROOT = './www'


def log_request(client_ip, request_line, status_code):
    """Write logs to the server.log file"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | {client_ip} | {request_line} | {status_code}\n"
    
    with open('server.log', 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(log_entry.strip())


def parse_headers(request_data):
    """Parse HTTP headers from request data"""
    lines = request_data.split('\r\n')
    headers = {}
    for line in lines[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
    return headers


def send_error(client_socket, code, connection="close"):
    """Send an error response"""
    if code == 400:
        body = "<h1>400 Bad Request</h1>"
        response = "HTTP/1.1 400 Bad Request\r\n"
    elif code == 403:
        body = "<h1>403 Forbidden</h1>"
        response = "HTTP/1.1 403 Forbidden\r\n"
    elif code == 404:
        body = "<h1>404 Not Found</h1><p>The requested file was not found.</p>"
        response = "HTTP/1.1 404 Not Found\r\n"
    else:
        # According to PDF: Five types of response statuses ONLY. 
        # Defaulting unknown to 400
        body = "<h1>400 Bad Request</h1>"
        response = "HTTP/1.1 400 Bad Request\r\n"
    
    response += f"Content-Length: {len(body)}\r\n"
    response += "Content-Type: text/html\r\n"
    response += f"Connection: {connection}\r\n"
    response += "\r\n"
    response += body
    client_socket.sendall(response.encode())


def get_content_type(filepath):
    """Determine Content-Type based on file extension"""
    if filepath.endswith('.html') or filepath.endswith('.htm'):
        return 'text/html'
    elif filepath.endswith('.txt'):
        return 'text/plain'
    elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
        return 'image/jpeg'
    elif filepath.endswith('.png'):
        return 'image/png'
    else:
        return 'application/octet-stream'


def handle_client(client_socket, client_addr):
    """Handle a single client request in a separate thread, supporting Keep-Alive"""
    client_ip = client_addr[0]
    print(f"Client Connection: {client_addr}")
    
    # Set a timeout for keep-alive connections
    client_socket.settimeout(10.0)

    try:
        while True:
            try:
                request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            except socket.timeout:
                break # Timeout waiting for next request on keep-alive connection
                
            if not request_data:
                break

            # Parse the request line
            lines = request_data.split('\r\n')
            if not lines or not lines[0]:
                break
                
            request_line = lines[0]
            parts = request_line.split(' ')

            if len(parts) != 3:
                send_error(client_socket, 400)
                log_request(client_ip, request_line, "400")
                break

            method = parts[0]
            path = parts[1]

            # Parse headers for If-Modified-Since and Connection
            headers = parse_headers(request_data)
            connection = headers.get('Connection', 'close').lower()

            # Support only GET and HEAD methods
            if method not in ['GET', 'HEAD']:
                send_error(client_socket, 400, connection)
                log_request(client_ip, f"{method} {path}", "400")
                if connection == 'close': break
                continue

            # Process path
            if path == '/':
                path = '/index.html'

                       # Security check: prevent directory traversal attacks
            file_path = os.path.join(WEB_ROOT, path[1:])
            real_path = os.path.realpath(file_path)
            web_root_real = os.path.realpath(WEB_ROOT)

            # Debug output
            # print(f"DEBUG: path={path}")
            # print(f"DEBUG: file_path={file_path}")
            # print(f"DEBUG: real_path={real_path}")
            # print(f"DEBUG: web_root_real={web_root_real}")
            # print(f"DEBUG: starts_with? {real_path.startswith(web_root_real)}")

            if not real_path.startswith(web_root_real):
                send_error(client_socket, 403, connection)
                log_request(client_ip, f"{method} {path}", "403")
                if connection == 'close': break
                continue

            # Check if file exists
            if not os.path.exists(real_path):
                send_error(client_socket, 404, connection)
                log_request(client_ip, f"{method} {path}", "404")
                if connection == 'close': break
                continue

            # Get file last modified time
            mtime = os.path.getmtime(real_path)
            last_modified = formatdate(mtime, usegmt=True)

            # Check If-Modified-Since header for 304 response
            if_modified_since = headers.get('If-Modified-Since')
            if if_modified_since and if_modified_since == last_modified:
                response = "HTTP/1.1 304 Not Modified\r\n"
                response += f"Connection: {connection}\r\n"
                response += "Content-Length: 0\r\n"
                response += "\r\n"
                client_socket.sendall(response.encode())
                print(f"{method} {path}: 304 Not Modified")
                log_request(client_ip, f"{method} {path}", "304")
                if connection == 'close': break
                continue

            # Read file content
            with open(real_path, 'rb') as f:
                file_content = f.read()

            content_type = get_content_type(real_path)

            # Build response with Last-Modified and Connection headers
            response = f"HTTP/1.1 200 OK\r\n"
            response += f"Content-Length: {len(file_content)}\r\n"
            response += f"Content-Type: {content_type}\r\n"
            response += f"Last-Modified: {last_modified}\r\n"
            response += f"Connection: {connection}\r\n"
            response += "\r\n"
            
            client_socket.sendall(response.encode())

            # Send file content only for GET requests
            if method == 'GET':
                client_socket.sendall(file_content)

            print(f"{method} {path}: 200 OK ({len(file_content)} bytes)")
            log_request(client_ip, f"{method} {path}", "200")
            
            if connection == 'close':
                break

    except Exception as e:
        print(f"Error processing request: {e}")
    finally:
        client_socket.close()


# ========== Main Server Entry Point ==========
if __name__ == '__main__':
    # Create www folder and default index.html if not exists
    if not os.path.exists(WEB_ROOT):
        os.makedirs(WEB_ROOT)
        with open(os.path.join(WEB_ROOT, 'index.html'), 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head><title>MyServer</title></head>
<body>
<h1>Hello from my web server!</h1>
<p>This server supports GET and HEAD requests.</p>
<p>It also handles Last-Modified, If-Modified-Since and Connection headers.</p>
</body>
</html>''')

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Server Startup: http://{HOST}:{PORT}")
    print(f"File Directory: {os.path.abspath(WEB_ROOT)}")
    print("Supported Methods: GET, HEAD")
    print("Supported Status Codes: 200, 304, 400, 403, 404")
    print("Press Ctrl+C to stop the server\n")

    try:
        while True:
            client_socket, client_addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_addr)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer has been shut down")
