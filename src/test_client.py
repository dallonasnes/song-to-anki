from flask import Flask
import json
import requests
import shutil
from urllib.parse import unquote
import pytest

from bs4 import BeautifulSoup

from .routes import configure_routes

def test_endpoint_bad_url_localfile():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?targetUrl=file:///users/file.txt'

    response = client.get(url)
    assert response.status_code == 400

def test_endpoint_bad_url_localhost():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?targetUrl=http://localhost:8080'

    response = client.get(url)
    assert response.status_code == 400

def test_endpoint_valid_url_but_not_lyricstranslate():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?targetUrl=https://google.com'

    response = client.get(url)
    assert response.status_code == 400

def test_endpoint_basic():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?targetUrl=https://lyricstranslate.com/en/dommage-too-bad.html'

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.get_data()) > 0

def test_endpoint_song_has_versions():
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()
    url = '/ankify-lyrics?targetUrl=https://lyricstranslate.com/en/comme-dhab-usual.html'

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.get_data()) > 0

def test_stress_test_short():
    """Tests the first 10 'New translations' on lyricstranslate.com"""
    app = Flask(__name__)
    configure_routes(app)
    client = app.test_client()

    endpoint = "/ankify-lyrics?targetUrl="
    root = "https://lyricstranslate.com"
    r = requests.get(root)
    soup = BeautifulSoup(r.content, "html.parser")
    div = soup.find_all("div", class_="front-new-translations block blockfront clear")[0]
    hrefs = div.find_all("a", href=True)[:-2] #cut off the last two hrefs, since they're links to support pages
    assert len(hrefs) == 10
    query_strings = [a['href'] for a in hrefs]
    urls = [unquote(endpoint + root + a) for a in query_strings]

    for url in urls:
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.get_data()) > 0
    
