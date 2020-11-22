import os

from flask import Flask

from routes import configure_routes

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)

# TODO
# 2. sync server-only proj back up with improvements to this api
# 3. delete log files periodically on pythonanywhere to save memory?
# 4. write options telling that pages that have the yellow tracking work best
# 5. to minify and combine js content just for fun?
# 6. Make everything a get instead of put request because free tier has higher limit for get requests
# 7. do this: https://learn.hashicorp.com/tutorials/terraform/lambda-api-gateway

# Need to validate incoming lyrics json obj to make sure nothing malicious
# Can do this with JWT - have client sent token to verify that my client-side code constructed the object

# Need to handle songs in multiple languages...eg danza kuduro is both portuguese and spanish
# Optionally add romanization to non-roman scripts
# Also add options page to contact me with bugs?
