from datetime import datetime
from flask import jsonify, request, send_from_directory
import validators
from .song_to_anki import SongLyric, Method

LYRICS_TRANSLATE = 'lyricstranslate.com'

def configure_routes(app):
    #####################################
    #HTTP Handlers
    #####################################
    @app.route("/song-req", methods=['PUT'])
    def song_req():
        pass

    @app.route("/ankify-lyrics", methods=['GET'])
    def ankify_lyrics():
        try:
            url = request.args.get('targetUrl').strip()
            #get and validate url before continuing
            if not validators.url(url) or LYRICS_TRANSLATE not in url.lower():
                raise Exception("Invalid url: " + url)

            song = SongLyric(url, Method.WORD_FREQ, api=True)
            try:
                song.populate_metadata()
                song.parse_text()
                song.build_mapping()
                song.build_anki_deck()
                song.write_anki_deck_to_file()
                #song.get_anki_deck_as_binary()

            except Exception as exc:
                song.finish(cleanup=True)
                raise exc
            
            response = send_from_directory(directory='.', filename=song.anki_deck_path)
            song.finish(cleanup=True)
            return response

        except Exception as ex:
            log_exception(ex)
            return json_failure({"exception": str(ex)})
            

######################################
#Helper methods
######################################

def json_failure(fields=None):
    if fields is None:
        fields = {}
    return jsonify({"success": False, **fields}), 400

def json_success(fields=None):
    if fields is None:
        fields = {}
    return jsonify({"success": True, **fields}), 200

def log_exception(exc):
    exc = str(exc)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    metadata_line = "*** Exception on " + dt_string + " \t***\n"
    end_line = "\t***\t\n"
    with (open("logs.txt", "a+")) as file:
        file.write(metadata_line)
        file.write(exc)
        file.write(end_line)