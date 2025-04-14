from app import app

# Pro Vercel serverless prostředí
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Flask aplikace je připravena!'.encode())

# Pro lokální spuštění
if __name__ == '__main__':
    app.run()
