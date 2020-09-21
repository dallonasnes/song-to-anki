from flask import Flask
import json
import requests
import shutil

from .routes import configure_routes

def test_endpoint_basic():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?songName=dommage&language=french&targetUrl=https://lyricstranslate.com/en/dommage-too-bad.html'

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.get_data()) > 0

def test_endpoint_song_has_versions():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?songName=comme_dhab&language=french&targetUrl=https://lyricstranslate.com/en/comme-dhab-usual.html'

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.get_data()) > 0