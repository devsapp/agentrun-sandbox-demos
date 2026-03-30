#!/usr/bin/env python3
"""
简单的 Echo Server
GET 请求返回 hello world
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# 默认端口
DEFAULT_PORT = 9000

class EchoHandler(BaseHTTPRequestHandler):
    """Echo 请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求，返回 hello world"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'ok\n')

def main():
    """主函数"""
    port = int(os.environ.get('ECHO_SERVER_PORT', DEFAULT_PORT))
    host = os.environ.get('ECHO_SERVER_HOST', '0.0.0.0')
    
    server = HTTPServer((host, port), EchoHandler)
    print(f"[echoserver] Starting echo server on {host}:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[echoserver] Shutting down echo server...")
        server.shutdown()

if __name__ == '__main__':
    main()
