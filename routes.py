from datetime import datetime
from flask import jsonify, request, send_from_directory, send_file
import json
import validators
import langcodes
from api import Lyrics, Text, ContentUrl
from sendgridAPI import send_email

import nltk

nltk.download("punkt")

LYRICS_TRANSLATE = "lyricstranslate.com"


def configure_routes(app):
    #####################################
    # HTTP Handlers
    #####################################
    @app.route("/lyrics-to-anki", methods=["PUT"])
    def song_req():
        try:
            obj = request.get_json()
            lyrics = obj["lyrics"]
            song_name = obj["song_name"]
            song_lang = obj["song_lang"]

            lyrics = Lyrics(lyrics, song_name, song_lang)
            lyrics.build_anki_deck()
            lyrics.build_anki_pkg()

            return send_file(
                lyrics.pkg,
                mimetype="application/apkg",
                as_attachment=True,
                attachment_filename=lyrics.song_name + ".apkg",
            )

        except Exception as ex:
            contentMsg = build_error_content_message(request, ex)
            subjectMsg = "server side exception"
            send_email(subjectMsg, contentMsg)
            log_server_exception(ex)
            return json_failure({"exception": str(ex)})

    @app.route("/log-client-error", methods=["PUT"])
    def log_client_error():
        try:
            obj = request.get_json()
            sendAlertIndicator = obj["sendAlert"]
            errorContext = obj["errorContext"]

            log_client_exception(errorContext)

            if sendAlertIndicator:
                contentMsg = build_error_content_message(request, errorContext)
                subjectMsg = "client side exception"
                send_email(subjectMsg, contentMsg)

            return json_success({"emailSent": sendAlertIndicator})

        except Exception as ex:
            contentMsg = build_error_content_message(request, ex)
            subjectMsg = "server side exception while logging exception from client"
            send_email(subjectMsg, contentMsg)
            log_server_exception(ex)
            return json_failure({"exception": str(ex)})

    @app.route("/mobile/content-to-anki/", methods=["PUT"])
    def anki_mobile_content_handler():
        try:
            obj = request.get_json()
            # TODO: cleanse and validate input
            text = obj["text"].strip()
            lang = obj["lang"].strip().lower()
            nonce = obj["nonce"].strip()
            # validate lang
            if not lang.isalpha():
                raise Exception("Invalid input language arguments: {}".format(lang))

            # TODO: right now language='en' hardcoded meaning client always sends language name written in english
            # this much be changed when the mobile app supports more language
            lang_code: str = langcodes.find(lang, language="en").language
            # NEXT: determine if text is a url
            if validators.url(text):
                content_obj = ContentUrl(lang_code, text, nonce)
                content_obj.hyderate_known_words()
                content_obj.process()
            else:
                text_obj = Text(lang_code, text, nonce)
                text_obj.hydrate_known_words()
                text_obj.tokenize()
                a_list = text_obj.get_anki_notes()

            return json_success({"notes": a_list, "lang": lang, "nonce": nonce})
        except Exception as ex:
            print(ex)
            return json_failure({"exception": str(ex)})


######################################
# Helper methods
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
    # with (open("logs.txt", "a+")) as file:
    #    file.write(metadata_line)
    #    file.write(exc)
    #    file.write(end_line)
    print(metadata_line)
    print(exc)
    print(end_line)


def log_client_exception(exc):
    exc = str(exc)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    metadata_line = "*** Exception on " + dt_string + " \t***\n"
    end_line = "\t***\t\n"
    # with (open("clientlogs.txt", "a+")) as file:
    #    file.write(metadata_line)
    #    file.write(exc)
    #    file.write(end_line)
    print(metadata_line)
    print(exc)
    print(end_line)


def build_error_content_message(req, ex):
    return "Input object is:\n {} \nand exception is\n {}".format(
        str(req.get_json()), str(ex)
    )
