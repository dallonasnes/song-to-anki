import os

from flask import Flask

from routes import configure_routes

app = Flask(__name__)

configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, port=8000)

#TODO
#Need to validate incoming lyrics json obj to make sure nothing malicious
#Can do this with JWT - have client sent token to verify that my client-side code constructed the object

#Need to handle songs in multiple languages...eg danza kuduro is both portuguese and spanish
#Optionally add romanization to non-roman scripts
#Also add options page to contact me with bugs?