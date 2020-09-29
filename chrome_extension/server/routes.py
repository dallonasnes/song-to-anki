from datetime import datetime
from flask import jsonify, request, send_from_directory
import json
from api import Lyrics

LYRICS_TRANSLATE = 'lyricstranslate.com'

def configure_routes(app):
    #####################################
    #HTTP Handlers
    #####################################
    @app.route("/lyrics-to-anki", methods=['PUT'])
    def song_req():
        try:
            import pdb; pdb.set_trace()
            obj = request.get_json()
            lyrics = obj['lyrics']
            song_name = obj['song_name']
            song_lang = obj['song_lang']

            lyrics = Lyrics(lyrics, song_name, song_lang)
            lyrics.build_anki_deck()
            lyrics.write_anki_deck_to_file()

            #import pdb; pdb.set_trace()
            response = send_from_directory(directory='.', filename=lyrics.anki_deck_path)
            lyrics.cleanup()
            return response

        except Exception as ex:
            print(ex)
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
