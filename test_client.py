from flask import Flask
import json
import requests
import shutil
from urllib.parse import unquote
import pytest

from routes import configure_routes

app = Flask(__name__)
configure_routes(app)

mobile_endpoint = "mobile/content-to-anki/"


def test_basic_use_mobile_endpoint():
    """Tests to ensure a 200 response for a basic use case"""

    client = app.test_client()
    # here text has three sentences
    text = "hello world. it's me. just wondering how you're doing these days?"
    data = {"lang": "english", "nonce": "1", "text": text}
    response = client.put(mobile_endpoint, json=data)

    assert response.status_code == 200
    resp_json = response.get_json()
    notes = resp_json["notes"]
    assert len(notes) == 3


def test_bad_language_input_mobile_endpoint():
    """Tests to ensure failure response code if language input is invalid"""

    client = app.test_client()
    # here text has three sentences
    text = "hello world. it's me. just wondering how you're doing these days?"
    data = {"lang": "not 4 realz", "nonce": "1", "text": text}
    response = client.put(mobile_endpoint, json=data)
    assert response.status_code == 400


def test_youtube_video_autosub_exists():
    """Tests to ensure basic functionality of building notes from a youtube video with autosubtitles"""
    client = app.test_client()
    url = "https://www.youtube.com/watch?v=OxTicIgXyKw"
    lang = "french"
    nonce = "1"

    data = {"lang": lang, "nonce": nonce, "text": url}
    response = client.put(mobile_endpoint, json=data)

    assert response.status_code == 200
    resp_json = response.get_json()
    notes = resp_json["notes"]
    assert len(notes) >= 261


def test_article():
    """Tests to ensure basic functionality of building notes from an article"""
    client = app.test_client()
    url = "https://www.lemonde.fr/idees/article/2020/11/25/loi-pluriannelle-de-programmation-de-la-recherche-un-rate-supplementaire-dans-la-triste-histoire-des-lois-relatives-aux-universites-depuis-mai-68_6061020_3232.html"
    lang = "french"
    nonce = "1"

    data = {"lang": lang, "nonce": nonce, "text": url}
    response = client.put(mobile_endpoint, json=data)

    assert response.status_code == 200
    resp_json = response.get_json()
    notes = resp_json["notes"]
    assert len(notes) > 0
