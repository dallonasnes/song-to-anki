from flask import Flask
import json
import requests
import shutil

from .routes import configure_routes

def test_endpoint():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?songName=dommage&language=french&targetUrl=https://lyricstranslate.com/en/dommage-too-bad.html'

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.get_data()) > 0