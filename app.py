import os

from flask import Flask

from routes import configure_routes

APP = Flask(__name__)

configure_routes(APP)

if __name__ == "__main__":
    APP.run(debug=True, port=8833)


#TODO:
"""
1) make python test client for rest api
2) deploy basic rest api to python anywhere -- NEEDS TO RUN SELENIUM, NEEDS A VM
    a) use Docker container 

3) try to hit it from browser
"""