from flask import Flask, request, jsonify, send_from_directory
import sys
import os

# Přidáme rodičovský adresář do systémové cesty, aby modul app byl nalezen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importujeme Flask aplikaci z app.py
from app import app

# Handler pro Vercel serverless funkce
def handler(request, response):
    return app(request, response)

# Export aplikace pro Vercel
app = app
