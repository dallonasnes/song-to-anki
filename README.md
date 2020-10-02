# song-to-anki

I like to learn languages by listening to music in foreign languages. By navigating to a song's line-by-line translation on lyricstranslate.com and, with the click of a button, this project generates a cloze_deletion Anki deck to help me memorize all the words I don't know in the song.

More specifically, the chrome extension builds a map of the song and translation lyrics, which it sends over HTTP to a flask rest api hosted (for free) on heroku. The server then generates cloze deletion sentences, builds a flash card deck and returns an APKG package to the client, ready for download and immediate import into Anki.

The `chrome_extension` directory contains code for both client and server. The `api` directory contains a server-only project, which I've used thus far to experiment with NLP and user customization, among other features.

This began as just a server-side project, using Docker to port code between my laptop and AWS, since running Chromium over SSH is a bit finnicky. But cloud serving was more than I wanted to pay, and asking my non-technical linguist friends to clone this repo and install Docker left this project inaccessible. So I made a lightweight version that does as much as possible on the client and thus simplified the server code enough to fit in the free tier of hosting.
