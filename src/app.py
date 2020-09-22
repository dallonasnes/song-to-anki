import os

from flask import Flask

from .routes import configure_routes

app = Flask(__name__)

configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, port=8000)

"""
TODO:
1) setup rest api like this: https://github.com/bellackn/airport_data
2) ci/git workflows: https://www.basefactor.com/github-actions-docker
3) use python's logging module
4) cleanup/productionize/minimize imports + dependencies + pip installs
5) make sure not to use names (named entity recog) as cloze cards
"""