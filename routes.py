import json
import io
from flask import jsonify, request, send_file
from datetime import datetime
from song_to_anki import SongLyric, Method

def configure_routes(app):
    #####################################
    #HTTP Handlers
    #####################################
    @app.route("/ankify-lyrics", methods=['GET'])
    def handle_text():
        try:
            url = request.args.get('targetUrl')
            songName = request.args.get('songName')
            language = request.args.get('language')

            song = SongLyric(url, songName, language, Method.WORD_FREQ)
            try:
                song.parse_text()
                song.build_mapping()
                song.build_anki_deck()
                song.get_anki_deck_as_binary()
                song.finish(cleanup=True)

            except Exception as exc:
                song.finish(cleanup=True)
                raise exc
            
            #to use this also need to uncomment song.get_anki_deck_as_binary() and set cleanup to True
            #return song.anki_deck, 200#json_success({"deck": json.dumps(song.anki_deck)})

            #using return method from https://gist.github.com/Miserlou/fcf0e9410364d98a853cb7ff42efd35a
            return send_file(
                    song.anki_deck,
                    attachment_filename=song.anki_deck_path,
                    as_attachment=True
                ), 200
            ##with open("song.anki_deck_path", "rb") as bites:
            #    return send_file(
            #        io.BytesIO(bites.read()),
            #        attachment_filename=song.anki_deck_path,
            #        as_attachment=True
            #    ), 200

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