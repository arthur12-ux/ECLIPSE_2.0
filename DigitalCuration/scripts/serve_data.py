"""scripts/serve_data.py

Small local static server helper to serve the repository files over HTTP.

Usage:
    python scripts/serve_data.py --port 8502

This starts a simple HTTP server bound to localhost. It's intentionally tiny
so you can open file links from the Streamlit UI reliably in your browser.
"""
import argparse
import http.server
import socketserver
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="Serve repository files over HTTP (for local UI links)")
    p.add_argument("--port", type=int, default=8502, help="Port to listen on (default: 8502)")
    p.add_argument("--bind", default="127.0.0.1", help="Address to bind to (default: 127.0.0.1)")
    args = p.parse_args()

    webroot = Path(__file__).resolve().parents[1]
    os.chdir(webroot)
    addr = args.bind
    port = args.port

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((addr, port), handler) as httpd:
        print(f"Serving {webroot} at http://{addr}:{port}/ (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stopping server")


if __name__ == "__main__":
    main()
