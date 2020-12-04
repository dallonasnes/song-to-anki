from genanki import Model
from genanki import Note
from genanki import Deck
from customPackage import Package
from typing import List, Set
from wordfreq import zipf_frequency
import langcodes
import nltk
import subprocess
import os
import requests
import pickle
from bs4 import BeautifulSoup

##############################
## Declarations
##############################
# ANKI card and deck preferences setup pasted from:
# https://github.com/kerrickstaley/genanki/blob/master/tests/test_cloze.py
CSS = """.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
.cloze {
 font-weight: bold;
 color: blue;
}
.nightMode .cloze {
 color: lightblue;
}
"""
MY_CLOZE_MODEL = Model(
    99887766174,
    "My Cloze Model",
    fields=[{"name": "Text"}, {"name": "Extra"}],
    templates=[
        {
            "name": "My Cloze Card",
            "qfmt": "{{cloze:Text}}",
            "afmt": "{{cloze:Text}}<br><br>{{Extra}}",
        }
    ],
    css=CSS,
    model_type=Model.CLOZE,
)

CLOZE_LIMIT = 2
MOBILE_CLOZE_LIMIT = 1
MIN_SENTENCE_LENGTH = 2
NO_SUBTITLES_WARNING = "video doesn't have subtitles"
WRITING_SUBTITLES_MSG = "Writing video subtitles to:"
DOWNLOADS = "downloads"
DATA = "data"

if not os.path.exists(DATA):
    os.makedirs(DATA)
if not os.path.exists(DOWNLOADS):
    os.makedirs(DOWNLOADS)

##############################
## Class Definition
##############################
class Lyrics:
    def __init__(self, lyrics, song_name, song_lang):
        self.lyrics = lyrics
        self.song_name = song_name
        self.song_lang = song_lang.lower()
        self.lang_code = langcodes.find(self.song_lang).language
        self.words_seen_in_this_deck = set()
        self.pkg = None

    def build_anki_deck(self):
        self.notes = []

        # this try catch block is a hack to deal with versioning issues
        # in the client-side code deployed as a chrome extension vs the one that I've updated in git
        try:
            # old version
            # self.lyrics holds a dictionary mapping lyrics to translated lyrics
            # issue here is that it doesn't keep lyrics in the correct order
            for lyric, translation in self.lyrics.items():
                cloze_sentence, translation = self.build_cloze_deletion_sentence(
                    lyric, translation
                )
                fields = [cloze_sentence, translation]
                my_cloze_note = Note(model=MY_CLOZE_MODEL, fields=fields)
                self.notes.append(my_cloze_note)
        except:
            # new version to solve lyric ordering issue
            # self.lyrics is a list of objects
            # where each object has key of song lyric and value of translated lyric
            for lyric_obj in self.lyrics:
                for lyric, translation in lyric_obj.items():
                    cloze_sentence, translation = self.build_cloze_deletion_sentence(
                        lyric, translation
                    )
                    fields = [cloze_sentence, translation]
                    my_cloze_note = Note(model=MY_CLOZE_MODEL, fields=fields)
                    self.notes.append(my_cloze_note)

        self.anki_deck = _build_deck(self.notes, self.song_name)

    def build_anki_pkg(self):
        self.pkg = Package(self.anki_deck).get_bytes()

    def build_cloze_deletion_sentence(self, lyric, translation):
        # cleanse of stop words and cloze words/phrases that aren't in my vocabulary (database? restAPI?)

        cloze_sentence = [word for word in lyric.split(" ")]

        # sometimes the last char of the last word in translation is a number referencing a footnote
        # delete that when it happens - but ensure the word isn't just a digit because that could be meaningful
        translation_tokens = translation.split(" ")
        last_word = translation_tokens[-1]
        if not last_word.isdigit() and last_word[-1].isdigit():
            last_word = last_word[:-1]
            translation_tokens[-1] = last_word

        # sort words from least frequent to most frequent based on freq score
        word_freq_scores = sorted(
            [
                (word, zipf_frequency(word.lower(), self.lang_code))
                for word in cloze_sentence
            ],
            key=lambda x: x[1],
        )
        assert len(word_freq_scores) == len(cloze_sentence)
        # make cloze out of first least-frequent word that isn't already in my vocabulary
        # get two rarest words for cloze
        count = 0
        for pair in word_freq_scores:
            rarest_word = pair[0]
            if rarest_word.lower() not in self.words_seen_in_this_deck:
                count += 1
                idx = cloze_sentence.index(rarest_word)
                # let's cut out all words in the first card only
                cloze_word = "{{c1::" + rarest_word + "}}"
                cloze_sentence[idx] = cloze_word
                self.words_seen_in_this_deck.add(rarest_word.lower())
                if count >= CLOZE_LIMIT:
                    break

        # if we didn't add any new words because all were seen, just make one cloze of rarest word
        if count == 0:
            rarest_word = word_freq_scores[0][0]
            idx = cloze_sentence.index(rarest_word)
            cloze_word = "{{c1::" + rarest_word + "}}"
            cloze_sentence[idx] = cloze_word

        return " ".join(cloze_sentence), " ".join(translation_tokens)


# TODO: some logic in this class is duplicated from the class above it
class ContentUrl:
    def __init__(self, lang_code, url, nonce):
        self.lang_code = lang_code
        self.url = url
        self.nonce = str(nonce)
        self.fileprefix = DOWNLOADS + "/" + self.nonce
        self.known_words = set()
        self.sentences = []  # populated in tokenize method
        self.cloze_sentences = []

    def hydrate_known_words(self):
        self.known_words: Set[str] = _hydrate_known_words(self.nonce, self.lang_code)

    def parse_vtt_file(self, file_path):
        with open(file_path, "r") as f:
            sentences = [
                x.strip()
                for x in f.readlines()
                if "</" not in x and "-->" not in x and len(x.strip()) > 0
            ]
            # dedup
            sentences = _dedup_list(sentences)
            return sentences

    def get_anki_notes(self):
        for sent in self.sentences:
            _build_cloze_sentence(
                sent, self.lang_code, self.known_words, self.cloze_sentences
            )
        # now that we've built all the cloze sentences, let's flush the updated known_words set to disk
        _flush_known_words_to_disk(self.known_words, self.nonce, self.lang_code)
        return self.cloze_sentences

    def process_link(self):
        # download article with beautiful soup
        article = requests.get(self.url).text
        soup = BeautifulSoup(article, "html.parser")
        a_list = nltk.tokenize.sent_tokenize(soup.text)
        sentences = [sent.strip() for sent in a_list]
        # dedup
        self.sentences = _dedup_list(sentences)

    def process_youtube(self):
        # first try to get manual subtitles
        # TODO: convert lang_code into lang_code used by youtube-dl
        process = subprocess.Popen(
            [
                "youtube-dl",
                self.url,
                "--skip-download",
                "--sub-lang",
                self.lang_code,
                "--sub-format",
                "vtt",
                "--write-sub",
                "-o",
                self.fileprefix,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = process.communicate()
        if NO_SUBTITLES_WARNING in str(err):
            # there were no manual subtitles, so try again for automatic subtitles
            process = subprocess.Popen(
                [
                    "youtube-dl",
                    self.url,
                    "--skip-download",
                    "--sub-lang",
                    self.lang_code,
                    "--sub-format",
                    "vtt",
                    "--write-auto-sub",
                    "-o",
                    self.fileprefix,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = process.communicate()
            if not WRITING_SUBTITLES_MSG in str(out):
                raise Exception("Can't get Youtube subtitles for video")

        file_path = str(self.fileprefix) + "." + str(self.lang_code) + ".vtt"
        try:
            self.sentences = self.parse_vtt_file(file_path)
            os.remove(file_path)
        except:
            os.remove(file_path)
            raise


# TODO: some logic in this class is duplicated from the class above it
class Text:
    def __init__(self, lang_code, text, nonce):
        self.lang_code = lang_code
        self.text = text
        self.nonce = nonce
        self.known_words = set()
        self.sentences = []  # populated in tokenize method
        self.cloze_sentences = []

    def tokenize(self):
        a_list = nltk.tokenize.sent_tokenize(self.text)
        # strip each sent from the tokenizer
        self.sentences = _dedup_list(
            [sent.strip() for sent in a_list]
        )  # dedup using set

    def get_anki_notes(self):
        for sent in self.sentences:
            _build_cloze_sentence(
                sent, self.lang_code, self.known_words, self.cloze_sentences
            )
        # now that we've built all the cloze sentences, let's flush the updated known_words set to disk
        _flush_known_words_to_disk(self.known_words, self.nonce, self.lang_code)
        return self.cloze_sentences

    def hydrate_known_words(self):
        # remember that known_words is a set
        self.known_words: Set[str] = _hydrate_known_words(self.nonce, self.lang_code)


##############################
## Helper Methods
##############################
def _dedup_list(sequence: List[str]) -> List[str]:
    seen = set()
    return [
        x for x in sequence if not (x in seen or seen.add(x))
    ]  # note that seen.add() -> None


def _hydrate_known_words(nonce: str, lang_code: str):
    rtn_val = set()
    try:
        with open(DATA + "/" + nonce + lang_code + ".pickle", "rb") as fp:
            rtn_val = set(pickle.load(fp))
    except:
        # file doesn't exist for this user + lang combo
        pass
    return rtn_val


def _flush_known_words_to_disk(known_words: Set[str], nonce: str, lang_code: str):
    try:
        filepath = DATA + "/" + nonce + lang_code + ".pickle"
        with open(filepath, "wb") as fp:
            pickle.dump(known_words, fp)
    except Exception as ex:
        print("failed to flush known words to disk")


def _build_cloze_sentence(
    sentence: str,
    lang_code: str,
    known_words: Set[str],
    output_cloze_sentences: List[str],
):

    # don't deal with sentences that are too short
    if len(sentence) < MIN_SENTENCE_LENGTH:
        return

    # TODO: what if there are "  " or more separating a word...or tabs etc? that may indicate a bad line with no useful language content
    cloze_sentence = [word for word in sentence.split(" ")]
    # TODO: revise this logic when i have storage working. because then may want most frequent unknown word
    # sort words from least frequent to most frequent based on freq score
    word_freq_scores = sorted(
        [(word, zipf_frequency(word.lower(), lang_code)) for word in cloze_sentence],
        key=lambda x: x[1],
    )
    assert len(word_freq_scores) == len(cloze_sentence)
    # make cloze out of first least-frequent word that isn't already in my vocabulary
    count = 0
    for pair in word_freq_scores:
        rarest_word = pair[0]
        if rarest_word.lower() not in known_words:
            count += 1
            idx = cloze_sentence.index(rarest_word)
            # let's cut out all words in the first card only
            cloze_word = "{{c1::" + rarest_word + "}}"
            cloze_sentence[idx] = cloze_word
            known_words.add(rarest_word.lower())
            if count >= MOBILE_CLOZE_LIMIT:
                # TODO: clean this up if we really only want one per sentence
                output_cloze_sentences.append(" ".join(cloze_sentence))
                break


def _build_deck(notes, deckname):
    """Builds anki deck out of notes. Returns anki deck object"""
    deck = Deck(deck_id=23, name=deckname)
    for note in notes:
        deck.add_note(note)
    return deck


if __name__ == "__main__":
    pass
