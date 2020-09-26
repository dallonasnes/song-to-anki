# song-to-anki

I like to learn languages by listening to music in foreign languages. Given a url to a song's line-by-line translation on lyricstranslate.com, this program generates a cloze_deletion Anki deck to help me memorize all the words I don't know in the song.

Here I used flask to build a REST API that takes a url and returns an APKG package, ready for import into Anki.

To give this a try, clone the repo and make sure your Docker installation has permissions to mount a volume to your directory of choice. Then run `bash build.sh` and `bash run.sh`. You can run the test suite with `pytest test_client.py` within the docker container.
