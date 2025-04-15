from app import app

# Pro Vercel serverless prostředí
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Načtení Flask aplikace z app.py
        from app import app as flask_app
        
        # Vytvořit odpověď
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Flask aplikace je připravena!'.encode())

    # Metoda pro zpracování všech HTTP requestů pro Vercel
    def __call__(self, req, res):
        # Tato metoda je volána Vercelem
        # Předáváme požadavek do Flask aplikace
        return app(req, res)

# Pro lokální spuštění
if __name__ == '__main__':
    app.run()
