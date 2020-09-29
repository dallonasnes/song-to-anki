# song-to-anki

I like to learn languages by listening to music in foreign languages. By navigating to a song's line-by-line translation on lyricstranslate.com, and with the click of a button, this project generates a cloze_deletion Anki deck to help me memorize all the words I don't know in the song. More specifically, the chrome extension builds a map of the song and translation lyrics, which it sends over HTTP to a flask rest api hosted (for free) on pythonanywhere.com. The server then generates cloze deletion sentences, generates a flash card deck and returns an APKG package to the client, ready for download and immediate import into Anki.

The `chrome_extension` directory contains code for both client and server. The `api` directory contains a server-only project, which I've used thus far to experiment with NLP and user customization, among other features.
