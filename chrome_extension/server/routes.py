from datetime import datetime
from flask import jsonify, request, send_from_directory
import json
from api import Lyrics
from sendgridAPI import send_email

LYRICS_TRANSLATE = 'lyricstranslate.com'

def configure_routes(app):
    #####################################
    #HTTP Handlers
    #####################################
    @app.route("/lyrics-to-anki", methods=['PUT'])
    def song_req():
        try:
            obj = request.get_json()
            lyrics = obj['lyrics']
            song_name = obj['song_name']
            song_lang = obj['song_lang']

            lyrics = Lyrics(lyrics, song_name, song_lang)
            lyrics.build_anki_deck()
            lyrics.write_anki_deck_to_file()

            response = send_from_directory(directory='.', filename=lyrics.anki_deck_path)
            lyrics.cleanup()
            return response

        except Exception as ex:
            contentMsg = get_error_content_message(request, ex)
            subjectMsg = "server side exception"
            send_email(subjectMsg, contentMsg)
            log_server_exception(ex)
            return json_failure({"exception": str(ex)})
    
    @app.route("/log-client-error", methods=['PUT'])
    def log_client_error():
        try:
            obj = request.get_json()
            sendAlertIndicator = obj['sendAlert']
            errorContext = obj['errorContext']

            log_client_exception(errorContext)

            if sendAlertIndicator:
                contentMsg = get_error_content_message(request, errorContext)
                subjectMsg = "client side exception"
                send_email(subjectMsg, contentMsg)
            
            return json_success({"emailSent": sendAlertIndicator})

        except Exception as ex:
            contentMsg = get_error_content_message(request, ex)
            subjectMsg = "server side exception while logging exception from client"
            send_email(subjectMsg, contentMsg)
            log_server_exception(ex)
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

def log_server_exception(exc):
    exc = str(exc)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    metadata_line = "*** Exception on " + dt_string + " \t***\n"
    end_line = "\t***\t\n"
    with (open("logs.txt", "a+")) as file:
        file.write(metadata_line)
        file.write(exc)
        file.write(end_line)
    
def log_client_exception(exc):
    exc = str(exc)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    metadata_line = "*** Exception on " + dt_string + " \t***\n"
    end_line = "\t***\t\n"
    with (open("clientlogs.txt", "a+")) as file:
        file.write(metadata_line)
        file.write(exc)
        file.write(end_line)

def get_error_content_message(req, ex):
    return "Input object is:\n {} \nand exception is\n {}".format(str(req.get_json()), str(ex))