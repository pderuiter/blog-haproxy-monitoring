#!/usr/bin/env python3
"""DEMO ONLY: answers 200 on every path, including /health."""
import http.server
import socketserver
import sys

BIND, PORT = sys.argv[1], int(sys.argv[2])


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"demo backend {PORT} {self.path}\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer((BIND, PORT), Handler).serve_forever()
