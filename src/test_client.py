from flask import Flask
import json
import requests
import shutil
from urllib.parse import unquote
import pytest

from bs4 import BeautifulSoup

from .routes import configure_routes

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
    hrefs = div.find_all("a", href=True)[:-2]
    assert len(hrefs) == 10
    query_strings = [a['href'] for a in hrefs]
    urls = [unquote(endpoint + root + a) for a in query_strings]

    failed = []
    #for url in urls:
    for idx in range(len(urls)):
        url = urls[idx]
        response = client.get(url)
        if response.status_code != 200:
            failed.append(url)
        else:
            assert len(response.get_data()) > 0
    
    import pdb; pdb.set_trace()

