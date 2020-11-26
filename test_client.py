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
