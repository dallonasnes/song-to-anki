from datetime import datetime
from flask import jsonify, request, send_from_directory
from .song_to_anki import SongLyric, Method

def configure_routes(app):
    #####################################
    #HTTP Handlers
    #####################################
    @app.route("/ankify-lyrics", methods=['GET'])
    def handle_text():
        try:
            url = request.args.get('targetUrl')
            song_name = request.args.get('songName')
            language = request.args.get('language')

            song = SongLyric(url, song_name, language, Method.WORD_FREQ)
            try:
                song.parse_text()
                song.build_mapping()
                song.build_anki_deck()
                song.write_anki_deck_to_file()
                song.get_anki_deck_as_binary()

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