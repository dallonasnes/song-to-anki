import sys
import os
import io
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from genanki import Model
from genanki import Note
from genanki import Deck
from genanki import Package

from time import sleep
import random
from datetime import datetime

from typing import Set, List
from enum import Enum

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
    'afmt': '{{cloze:Text}}<br>{{Extra}}',
  },],
  css=CSS,
  model_type=Model.CLOZE)

def _wr_apkg(notes, deckname):
    """Write cloze cards to an Anki apkg file"""
    deck = Deck(deck_id=23, name=deckname)
    for note in notes:
        deck.add_note(note)
    fout_anki = '{NAME}.apkg'.format(NAME=deckname)
    print("TODO: How can I return as binary instead of writing it then having to delete it")
    Package(deck).write_to_file(fout_anki)
    print('  {N} Notes WROTE: {APKG}'.format(N=len(notes), APKG=fout_anki))
    return fout_anki

class Method(Enum):
    NAIVE = 0
    NLP = 1
    WORD_FREQ = 2

CLOZE_LIMIT = 2

class SongLyric():

    def __init__(self, url, song_name, lang, method=Method.NAIVE):
        self.url = url
        self.song_name = song_name
        self.lang = lang.lower()
        self.vocab_filename = self.lang + "vocab.txt"
        self.lang_code = self._get_lang_code()
        self.method = method

        if self.method == Method.NLP:
            import spacy
            #only need these things if not using naive method of creating cloze deletion cards
            self.nlp = _try_get_nlp_for_lang(lang)
            self.stop_words = _get_stop_words_for_lang(lang)
        
        if self.method != Method.NAIVE:
            self.words_seen_in_this_deck = set()
            self.my_vocabulary: Set[str] = _get_my_vocab_for_lang(self.vocab_filename)

        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)

    def _get_lang_code(self):
        if self.lang == "french":
            return "fr"
        else:
            raise NotImplementedError("Lang code not yet implemented for language: " + str(self.lang))

    def parse_text(self):
        self.driver.get(self.url)
        sleep(1)

        #wait for load
        self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="lyrics-preview"]/p/a')))
        self.driver.find_element_by_xpath('//*[@id="lyrics-preview"]/p/a').click()
        #is the below line really necessary
        self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="songtranslation"]/div[2]')))

        sleep(1)
        #get "ltf" classes -> there should be 2, one for song lyrics and other for translation lyrics
        lyrics = self.driver.find_elements_by_class_name("ltf")

        def line_filter(line):
            return len(line.strip()) > 0 and '[' not in line
        self.translation_lyrics = list(filter(line_filter, lyrics[0].text.split('\n')))
        self.song_lyrics = list(filter(line_filter, lyrics[1].text.split('\n')))

        assert len(self.song_lyrics) == len(self.translation_lyrics)
    
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
        with io.open(path, "rb") as f:
            content = f.read()
        self.anki_deck = content

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

        self.anki_deck_path = _wr_apkg(self.notes, self.song_name)
    
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
            from wordfreq import zipf_frequency
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
        
        #overwrite my vocabulary text file with the udpated one
        if self.method != Method.NAIVE and not cleanup:
            _overwrite_vocab_file(self.vocab_filename, self.words_seen_in_this_deck, self.song_name)
        
        if cleanup:
            try:
                os.remove(self.vocab_filename)
                os.remove(self.anki_deck_path)
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
    metadata_line = "*** new vocabulary from song " + songname + " written on " + dt_string + "***\n"
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
    if len(args) == 4:
        url = args[1]
        song_name = args[2]
        lang = args[3]
        song = SongLyric(url, song_name, lang, Method.WORD_FREQ)
        try:
            song.parse_text()
            song.build_mapping()
            song.build_anki_deck()
        finally:
            song.finish()
    elif len(args) == 1:
        #BASIC TEST MODE
        url = "https://lyricstranslate.com/en/sac-%C3%A0-dos-backpack.html"
        song_name = "sac a dos - bigflo&oli"
        lang = "french"
        song = SongLyric(url, song_name, lang, Method.WORD_FREQ)
        try:
            song.parse_text()
            song.build_mapping()
            #song.align_text_with_audio()
            song.build_anki_deck()
            #song.visualize()
        finally:
            song.finish()
    else:
        print("Usage: LyricsTranslate_url{1} song_name{2} language{3}")
