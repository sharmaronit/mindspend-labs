"""
Super simple HTTP server using Python's built-in http.server
This is just to test if ANY server can run on this system
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({'status': 'healthy'})
            self.wfile.write(response.encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({'message': 'Server is running'})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

if __name__ == '__main__':
    server_address = ('127.0.0.1', 8001)
    httpd = HTTPServer(server_address, SimpleHandler)
    print("🚀 Simple HTTP Server starting...")
    print(f"📍 Running on http://127.0.0.1:8001")
    print("🔍 This is using Python's built-in http.server")
    print("⏳ Waiting for connections... (Press CTRL+C to stop)")
    print()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
