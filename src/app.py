import os

from flask import Flask

from .routes import configure_routes

app = Flask(__name__)

configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, port=8833)

#TODO:
"""
2) test get attribute method only to see if that is most consistent for getting == number of lyrics
3) use logging module
4) cleanup/productionize/minimize imports + dependencies + pip installs
5) ci/git workflows
"""