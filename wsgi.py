from app import app

# Pro Vercel serverless prostředí
def handler(event, context):
    """
    Serverless funkce pro Vercel - slouží jako vstupní bod pro WSGI aplikaci.
    """
    return app

# Pro lokální spuštění
if __name__ == '__main__':
    app.run()
