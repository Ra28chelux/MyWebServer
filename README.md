# Comp 2322 Computer Networking - Multi-thread Web Server

## Project Description
This project is a multi-threaded Web Server implemented in Python using basic socket programming (without using the high-level `HTTPServer` class). It is designed to handle multiple concurrent HTTP requests from clients (e.g., web browsers, `curl`). 

The server supports:
- **Methods:** `GET`, `HEAD`
- **File Types:** Text files (`.html`, `.txt`) and Image files (`.jpg`, `.png`)
- **Response Status Codes (5 strictly supported):** 
  - `200 OK`
  - `304 Not Modified`
  - `400 Bad Request`
  - `403 Forbidden`
  - `404 Not Found`
- **Headers Handled:** `Last-Modified`, `If-Modified-Since`, `Connection` (Keep-Alive / Close)
- **Logging:** All client requests are logged in `server.log`.


## Prerequisites
- **Python 3.x** is required.
- No third-party libraries are needed (only built-in modules: `socket`, `os`, `threading`, `time`, `email.utils`).


## How to Run the Server

1. Open a terminal or command prompt.
2. Navigate to the directory containing the server script (`server.py`).
3. Run the following command:
   ```bash
   python server.py
4. Open your browser and visit:
   http://127.0.0.1:8889


## Testing the Server

Use the following `curl` commands to test different features:

### 1. GET Request (Text File)
```bash
curl http://127.0.0.1:8889/
```

### 2. GET Request (Image File)
```bash
curl http://127.0.0.1:8889/test.jpg
```

### 3. HEAD Request
```bash
curl -I http://127.0.0.1:8889/
```
### 4. 304 Not Modified (Conditional Request)
```bash
# First, get the Last-Modified value from the response
curl -v http://127.0.0.1:8889/ 2>&1 | grep "Last-Modified"

# Then use it in the If-Modified-Since header
curl -v -H "If-Modified-Since: Sat, 04 Apr 2026 15:11:11 GMT" http://127.0.0.1:8889/
```

### 5. 404 Not Found
```bash
curl -I http://127.0.0.1:8889/nonexistent.html
```
## Log File

All requests are logged to `server.log` in the following format:

timestamp | client_ip | requesti_line | status_code

Example:

2026-04-05 21:39:08 | 127.0.0.1 | GET /index.html | 200
2026-04-05 21:40:13 | 127.0.0.1 | GET /index.html | 304

## Author
- Name: Li Yizhen
- Student ID: 24103965D
- Course: COMP2322 Computer Networking
