#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir('/Users/moadigitalagency/IPTV-Afrika-New')

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅ Serveur HTTP démarré sur http://localhost:{PORT}")
    print(f"📂 Servant depuis: {os.getcwd()}")
    print(f"🔗 Ouvre: http://localhost:{PORT}/templates/index.html")
    httpd.serve_forever()
