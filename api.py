from genanki import Model
from genanki import Note
from genanki import Deck
from customPackage import Package

from wordfreq import zipf_frequency
import langcodes

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

CLOZE_LIMIT = 2

##############################
## Class Definition
##############################
class Lyrics():

    def __init__(self, lyrics, song_name, song_lang):
        self.lyrics = lyrics
        self.song_name = song_name
        self.song_lang = song_lang.lower()
        self.lang_code = langcodes.find(self.song_lang).language
        self.words_seen_in_this_deck = set()
        self.pkg = None

    def build_anki_deck(self):
        self.notes = []

        #this try catch block is a hack to deal with versioning issues
        #in the client-side code deployed as a chrome extension vs the one that I've updated in git
        try:
            #old version
            #self.lyrics holds a dictionary mapping lyrics to translated lyrics
            #issue here is that it doesn't keep lyrics in the correct order
            for lyric, translation in self.lyrics.items():
                cloze_sentence, translation = self.build_cloze_deletion_sentence(lyric, translation)
                fields = [cloze_sentence, translation]
                my_cloze_note = Note(model=MY_CLOZE_MODEL, fields=fields)
                self.notes.append(my_cloze_note)
        except:
            #new version to solve lyric ordering issue
            #self.lyrics is a list of objects
            #where each object has key of song lyric and value of translated lyric
            for lyricObj in self.lyrics:
                for lyric, translation in lyricObj.items():
                    cloze_sentence, translation = self.build_cloze_deletion_sentence(lyric, translation)
                    fields = [cloze_sentence, translation]
                    my_cloze_note = Note(model=MY_CLOZE_MODEL, fields=fields)
                    self.notes.append(my_cloze_note)

        self.anki_deck = _build_deck(self.notes, self.song_name)
        
    def build_anki_pkg(self):
        self.pkg = Package(self.anki_deck).get_bytes()
    
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

        #sort words from least frequent to most frequent based on freq score
        word_freq_scores = sorted([(word, zipf_frequency(word.lower(), self.lang_code)) for word in cloze_sentence], key=lambda x: x[1])
        assert len(word_freq_scores) == len(cloze_sentence)
        #make cloze out of first least-frequent word that isn't already in my vocabulary
        #get two rarest words for cloze
        count = 0
        for pair in word_freq_scores:
            rarest_word = pair[0]
            if rarest_word.lower() not in self.words_seen_in_this_deck:
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

        return ' '.join(cloze_sentence), ' '.join(translation_tokens)


##############################
## Helper Methods
##############################
def _build_deck(notes, deckname):
    """Builds anki deck out of notes. Returns anki deck object"""
    deck = Deck(deck_id=23, name=deckname)
    for note in notes:
        deck.add_note(note)
    return deck

if __name__ == "__main__":
    pass