#!/usr/bin/env python3
"""Tiny static file server for local preview of the CAEM dashboard (no deps).
Serves this folder at http://127.0.0.1:8012 . On the real host just upload the folder."""
import os, http.server, socketserver
os.chdir(os.path.dirname(os.path.abspath(__file__)))
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 8012), http.server.SimpleHTTPRequestHandler) as httpd:
    httpd.serve_forever()
