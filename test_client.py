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
    data = {
        "lang": "english",
        "nonce": "1",
        "text": "hello world. it's me. just wondering how you're doing these days?",
    }
    response = client.put(mobile_endpoint, json=data)

    assert response.status_code == 200
