import sys
import os
import io
import requests
import uuid
from zipfile import ZipFile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from pyvirtualdisplay import Display

from genanki import Model
from genanki import Note
from genanki import Deck
from genanki import Package

from time import sleep
import random
from datetime import datetime

from typing import Set, List
from enum import Enum

from wordfreq import zipf_frequency
import langcodes
from bs4 import BeautifulSoup

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
  'My Cloze Model',
  fields=[
    {'name': 'Text'},
    {'name': 'Extra'},
  ],
  templates=[{
    'name': 'My Cloze Card',
    'qfmt': '{{cloze:Text}}',
    'afmt': '{{cloze:Text}}<br><br>{{Extra}}',
  },],
  css=CSS,
  model_type=Model.CLOZE)

def _build_deck(notes, deckname):
    """Builds anki deck out of notes. Returns anki deck object"""
    deck = Deck(deck_id=23, name=deckname)
    for note in notes:
        deck.add_note(note)
    return deck

def _wr_apkg(deck, deckname):
    """Writes deck to Anki apkg file
        @params: anki deck object, deckname
        @returns path to output dec
    """
    fout = 'decks/{NAME}.apkg'.format(NAME=deckname)
    pkg = Package(deck)
    pkg.write_to_file(fout)
    print('  {N} Notes WROTE: {APKG}'.format(N=len(deck.notes), APKG=fout))
    return fout

def _zip_apkg(deck_path):
    fout_zip = deck_path + '.zip'
    ZipFile(fout_zip, mode='w').write(deck_path)
    return fout_zip

class Method(Enum):
    NAIVE = 0
    NLP = 1
    WORD_FREQ = 2

CLOZE_LIMIT = 2
MAX_RETRIES = 5

def _line_filter(line):
    return len(line.strip()) > 0 and '[' not in line

class SongLyric():

    def __init__(self, url, method=Method.NAIVE, api=False):
        self.url = url
        self.method = method
        self.api = api
        self.anki_deck_path = None
        self.display = None
        self.vocab_filename = None
        self.song_name = None
        self.lang = None
        self.lang_code = None

        #chromedriver setup
        options = Options()

        if api:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

            #options.headless = True
            options.add_argument('--disable-extensions')
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_experimental_option('prefs', {
            'download.default_directory': os.getcwd(),
            'download.prompt_for_download': False,
            })

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)

    def populate_metadata(self):
        self.driver.get(self.url)
        
        sleep(1)
        song_name = self.driver.find_element_by_class_name("song-node-info-album").find_element_by_tag_name("a").text
        try:
            lang = self.driver.find_element_by_class_name("song-langs-preview-visible").text.lower()
        except:
            lang = self.driver.find_elements_by_class_name("langsmall-song")[1].text.lower().split('\n')[0].strip().split(' ')[0]

        self.song_name = song_name
        self.lang = lang.lower().strip()
        self.vocab_filename = "vocabs/" + self.lang + uuid.uuid4().hex + "vocab.txt"
        self.lang_code = self._get_lang_code()

        if self.method == Method.NLP:
            import spacy
            #only need these things if not using naive method of creating cloze deletion cards
            self.nlp = _try_get_nlp_for_lang(self.lang)
            self.stop_words = _get_stop_words_for_lang(self.lang)
        
        if self.method != Method.NAIVE:
            self.words_seen_in_this_deck = set()
            self.my_vocabulary: Set[str] = _get_my_vocab_for_lang(self.vocab_filename)

    def _get_lang_code(self):
        return langcodes.find(self.lang).language
    
    def _get_lyrics(self):
        """Idea: only add sentence to (both) lyrics arrays when the line's unique id exists in both arrays of ids"""
        #wait for load
        sleep(1)
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="lyrics-preview"]/p/a')))
            self.driver.find_element_by_xpath('//*[@id="lyrics-preview"]/p/a').click()
            sleep(1)
        except:
            pass

        #get "ltf" classes -> there should be 2, one for song lyrics and other for translation lyrics
        lyrics = self.driver.find_elements_by_class_name("ltf")
        x = lyrics[1].find_elements_by_tag_name("div")
        y = lyrics[0].find_elements_by_tag_name("div")

        song_lyrics = [a.text for a in x]
        tr_lyrics = [a.text for a in y]

        song_ids = [a.get_attribute("class") for a in x]
        tr_ids = [a.get_attribute("class") for a in y]

        #make sure we didn't lose any data in getting texts and ids
        assert len(song_lyrics) == len(song_ids)
        assert len(tr_lyrics) == len(tr_ids)

        filtered_song_ids = [a for a in song_ids if 'll' in a]
        filtered_tr_ids = [a for a in tr_ids if 'll' in a]

        #lambda fn converts "ll-12-3" into 1203 to correctly sort 12>11 and 3>2
        all_ids = sorted(list(set(filtered_song_ids).intersection(set(filtered_tr_ids))), key=lambda x: (100*int(x.split('-')[1]) + int(x.split('-')[2]) ))

        self.song_lyrics = []
        self.translation_lyrics = []
        for id in all_ids:
            if id in song_ids and id in tr_ids:
                song_lyric_idx = song_ids.index(id)
                tr_lyric_idx = tr_ids.index(id)

                song_lyric = song_lyrics[song_lyric_idx]
                tr_lyric = tr_lyrics[tr_lyric_idx]

                #don't want to make cards for thinks like "[refrain]"
                if '[' not in song_lyric and '[' not in tr_lyric:
                    self.song_lyrics.append(song_lyric)
                    self.translation_lyrics.append(tr_lyric)

    def parse_text(self):
        self._get_lyrics()

        if len(self.song_lyrics) != len(self.translation_lyrics):
            #check for different versions and try all versions until one works
            other_versions = self.driver.find_element_by_xpath('//*[@id="translittab"]').find_elements_by_tag_name('a')
            for version in other_versions:
                #click to get that version
                version.click()
                #retry get lyrics from page
                self._get_lyrics()

                if len(self.song_lyrics) == len(self.translation_lyrics):
                    break

        assert len(self.song_lyrics) == len(self.translation_lyrics)
        assert len(self.song_lyrics) > 0

    
    def build_mapping(self):
        self.mapping = {}
        for idx in range(len(self.song_lyrics)):
            song_lyric = self.song_lyrics[idx]
            translation = self.translation_lyrics[idx]
            self.mapping[song_lyric] = translation
    
    def align_text_with_audio(self):
        pass

    def get_anki_deck_as_binary(self):
        path = self.anki_deck_path
        with open(path, "rb") as bites:
            self.anki_deck = io.BytesIO(bites.read())

    def visualize(self):
        #render HTML and JS such that words are highlighted as they are said in song
        #song pauses upon reaching a cloze deletion, waiting for user to fill the word in
        pass

    def build_anki_deck(self):
        self.notes = []
        for lyric, translation in self.mapping.items():
            #build cloze sentence by naively grabbing the first word
            cloze_sentence, translation = self.build_cloze_deletion_sentence(lyric, translation)
            fields = [cloze_sentence, translation]
            my_cloze_note = Note(model=MY_CLOZE_MODEL, fields=fields)
            self.notes.append(my_cloze_note)

        self.anki_deck = _build_deck(self.notes, self.song_name)
        
    def write_anki_deck_to_file(self):
        self.anki_deck_path = _wr_apkg(self.anki_deck, self.song_name)
    
    def build_cloze_deletion_sentence(self, lyric, translation):
        #cleanse of stop words and cloze words/phrases that aren't in my vocabulary (database? restAPI?)
        
        cloze_sentence = [word for word in lyric.split(' ')]
        #sometimes the last char of the last word in translation is a number referencing a footnote
        #delete that when it happens - but ensure the word isn't just a digit because that could be meaningful
        translation_tokens = translation.split(' ')
        last_word = translation_tokens[-1]
        if not last_word.isdigit() and last_word[-1].isdigit():
            last_word = last_word[:-1]
            translation_tokens[-1] = last_word

        #naive implementation first - just use the first word
        if self.method == Method.NAIVE:
            first_word = cloze_sentence[0]
            cloze = "{{c1::" + first_word +"}}"
            cloze_sentence[0] = cloze

        elif self.method == Method.WORD_FREQ:
            #sort words from least frequent to most frequent based on freq score
            word_freq_scores = sorted([(word, zipf_frequency(word, self.lang_code)) for word in cloze_sentence], key=lambda x: x[1])
            assert len(word_freq_scores) == len(cloze_sentence)
            #make cloze out of first least-frequent word that isn't already in my vocabulary
            #TODO: should I deal with lemmas instead?
            #TODO: should I deal with word phrases instead?
            #get two rarest words for cloze
            count = 0
            for pair in word_freq_scores:
                rarest_word = pair[0]
                if rarest_word.lower() not in self.my_vocabulary and rarest_word.lower() not in self.words_seen_in_this_deck:
                    count += 1
                    idx = cloze_sentence.index(rarest_word)
                    #let's cut out all words in the first card only
                    cloze_word = "{{c1::" + rarest_word +"}}"
                    cloze_sentence[idx] = cloze_word
                    self.words_seen_in_this_deck.add(rarest_word.lower())
                    if count >= CLOZE_LIMIT:
                        break
            
            #if we didn't add any new words because all were seen, just make one cloze of rarest word
            if count == 0:
                rarest_word = word_freq_scores[0][0]
                idx = cloze_sentence.index(rarest_word)
                cloze_word = "{{c1::" + rarest_word +"}}"
                cloze_sentence[idx] = cloze_word

        elif self.method == Method.NLP:
            #first build array of lemmas
            lemmas = [token.lemma_ for token in self.nlp(lyric) if not token.is_punct]
            #assert len(lemmas) != len(cloze_sentence)
            if len(lemmas) != len(cloze_sentence):
                import pdb; pdb.set_trace()
            else:

                count = 1
                for idx in range(len(cloze_sentence)):
                    word = cloze_sentence[idx]
                    if word.lower() not in self.stop_words:
                        word_stem = lemmas[idx] #get infinitive so that we can match regardless of case/conjugation
                        if word_stem.lower() not in self.my_vocabulary and word_stem.lower() not in self.words_seen_in_this_deck:
                            cloze_word = "{{c" + str(count) + "::" + word +"}}"
                            cloze_sentence[idx] = cloze_word
                            self.words_seen_in_this_deck.add(word_stem.lower())
                            count += 1 #so that next iteration does c2 instead of c1
        
        return ' '.join(cloze_sentence), ' '.join(translation_tokens)
    
    def finish(self, cleanup=False):
        self.driver.quit()
        if self.display: self.display.stop()
        #overwrite my vocabulary text file with the udpated one
        if self.method != Method.NAIVE and not cleanup:
            _overwrite_vocab_file(self.vocab_filename, self.words_seen_in_this_deck, self.song_name)
        
        if cleanup:
            try:
                if self.vocab_filename: os.remove(self.vocab_filename)
                if self.anki_deck_path: os.remove(self.anki_deck_path)
            except OSError:
                pass

def _try_get_nlp_for_lang(lang):
    if lang == "french":
        return spacy.load('fr_core_news_sm')
    else:
        raise NotImplementedError("Language model not yet implemented for " + str(lang))

def _get_my_vocab_for_lang(filename):
    vocab = []
    try:
        with (open(filename, "r")) as file:
            #NB: *** delineates metadata in text file
            vocab = [x.strip() for x in file.readlines() if '***' not in x]
    except FileNotFoundError:
        with (open(filename, "a+")) as file:
            pass #do nothing, just create the file
    return set(vocab)

def _overwrite_vocab_file(filename, words_seen: Set, songname: str):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    metadata_line = "*** new vocabulary from song " + songname + " written on " + dt_string + " ***\n"
    with (open(filename, "a+")) as file:
        file.write(metadata_line)
        [file.write(line + '\n') for line in list(words_seen)]

def _get_stop_words_for_lang(lang):
    stop_words = set()
    if lang == "french":
        from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop
        [stop_words.add(word) for word in fr_stop]
    
    return stop_words

        

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        url = args[1]
        song = SongLyric(url, Method.WORD_FREQ)
        try:
            song.populate_metadata()
            song.parse_text()
            song.build_mapping()
            song.build_anki_deck()
            song.write_anki_deck_to_file()
        except Exception as ex:
            print(ex)
            import pdb; pdb.set_trace()
        finally:
            song.finish(cleanup=False)
    else:
        print("Usage: LyricsTranslate_url{1}")
