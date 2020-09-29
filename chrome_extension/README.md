# Song to Anki chrome extension

Here live the client and server codes. To spin up the flask server, `cd` into the `server` directory, `pip install -r reqs.txt` to import required modules (do this in a virtual environment) and then run `python app.py`.

To test out the client, load the `client` directory into `chrome://extensions` and give it a whirl.

What's exciting about this project is the logging and alerting I've put in. In addition to logging all exceptions and errors, I'm using sendgrid to send me an email whenever critical or otherwise "I didn't think this would fail" errors take place.

For logging and alerting errors on the client, I funneled exceptions and bad states into a function that sent them to my `log-client-error` endpoint, which added them to logs and sent out an alert depending on severity.
