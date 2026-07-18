import random

from wonderwords import RandomWord


rw = RandomWord()

GRAMMAR = {
    "Sent": [
        ["Clause", "."],
        ["Clause", ",", "PrepPhrase", "."],
        ["PrepPhrase", ",", "Clause", "."],
        # ["QuestionClause", "?"]
    ],

    "Clause": [
        ["SimpleClause"],
        ["SimpleClause"],
        ["SimpleClause", "Conj", "SimpleClause"]
    ],

    "SimpleClause": [
        ["NounPhrase", "VerbPhrase"],
        ["Verb", "NounPhrase"],
        ["NounPhrase", "Aux", "Predicate"],
        ["NounPhrase", "Aux", "VerbPhrase"],
        ["NounPhrase", "VerbPhrase", "until", "NounPhrase", "VerbPhrase"],
        ["Noun", "that", "VerbPhrase"]
    ],

    "QuestionClause": [
        ["Aux", "NounPhrase", "Verb"]
    ],

    "Predicate": [
        ["Adj"],
        ["NounPhrase"]
    ],

    "NounPhrase": [
        ["Det", "Noun"],
        ["Det", "Noun"],
        ["Det", "Noun", "and", "Noun"],
        ["Det", "Noun", ",", "Noun", ",",  "and", "Noun"],
        ["Det", "Adj", "Noun"],
        ["Det", "Adj", "Noun"],
        ["Det", "Adj", "Conj", "Adj", "Noun"],
        ["Pron"],
        ["Pron"],
        ["Det", "Noun", "PrepPhrase"],
        ["Det", "Noun", "PrepPhrase"],
    ],

    "VerbPhrase": [
        ["Verb"],
        ["Verb", "NounPhrase"],
        ["Verb", "Adv"],
        ["Verb", "NounPhrase", "PrepPhrase"],
        ["Verb", "PrepPhrase"],
    ],

    "PrepPhrase": [
        ["Prep", "NounPhrase"]
    ],
}


class Lexicon:
    lexicon = {
        "Det": ["the", "a", "this", "those", "my", "our", "your", "its"],
        "Prep": ["of", "in", "with", "by", "after", "before"],
        "Conj": ["and", "but", "while", "yet"],
        "Aux": ["is", "was", "has", "will"],
        "Pron": ["it", "they", "which", "he", "she"],
        "Adv": ["quietly", "briefly", "loosely"]
    }

    rw_code = {
        "Noun": "noun", "Verb": "verb", "Adj": "adjective"
    }

    def __init__(self, word_bank: list):
        self.inventory = False
        self.retention = 0
        self.sentence_history = []
        self.word_bank = word_bank

    def gen_word(self, target_pos: str, custom_skew: int = 0) -> str:
        try:
            if random.randrange(3) <= custom_skew:
                return random.choice([word for word, pos in self.word_bank if pos == target_pos])

        except IndexError:
            pass

        return rw.word(include_parts_of_speech=(self.rw_code[target_pos],))

    def gen_topic(self, retention: int = 4):
        topic_words, topic_poss = gen_sentence(self)

        self.retention = retention
        self.inventory = {
            "Noun": [], "Verb": [], "Adj": []
        }

        for pos in self.inventory:
            self.inventory[pos] = [[topic_words[i], retention] for i in range(len(topic_words)) if topic_poss[i] == pos]

            while len(self.inventory[pos]) < 3:
                self.inventory[pos].append([self.gen_word(pos, 1), retention])

        return topic_words

    def _grab_from_inventory(self, pos: str, depth: int = 0) -> list[str]:
        if random.randrange(2) == 0 and self.inventory:
            i = random.choice(range(len(self.inventory[pos])))
            word, retention = self.inventory[pos][i]

            new_retention = retention - random.randrange(0, 2)

            if new_retention > 0:
                self.inventory[pos][i] = (word, new_retention)

            else:
                self.inventory[pos][i] = (self.gen_word(pos), self.retention)

        else:
            word = self.gen_word(pos)

        if word in self.sentence_history and depth < 10:
            return self._grab_from_inventory(pos, depth + 1)

        else:
            self.sentence_history.append(word)
            return [word]

    def forget_sentence_history(self):
        self.sentence_history = []

    def __getitem__(self, item: str) -> list[str]:
        if item in ("Noun", "Verb", "Adj"):
            return self._grab_from_inventory(item)

        else:
            return self.lexicon.get(item, [item])

    def __contains__(self, item: str) -> bool:
        return item in self.lexicon or item in ("Noun", "Verb", "Adj")


def expand(symbol: str, context: Lexicon):
    if symbol not in GRAMMAR:
        return [random.choice(context[symbol])], [symbol]

    rule = random.choice(GRAMMAR[symbol])
    words = []
    poss = []

    for sym in rule:
        word, pos = expand(sym, context)
        words.extend(word)
        poss.extend(pos)

    return words, poss


def gen_sentence(context: Lexicon):
    return expand("Sent", context)


def clean_sentence(words: list) -> str:
    sentence = " ".join(words)

    for punct in (".", ",", "?", "!"):
        sentence = sentence.replace(f" {punct}", punct)

    for vowel in ("a", "i", "o", "u", "y", "e"):
        sentence = sentence.replace(f" a {vowel}", f" an {vowel}")

    return sentence.capitalize()


def gen_paragraph(n_sentences: int, word_bank: list, break_into_paragraphs: bool = False) -> str:
    lexicon = Lexicon(word_bank)
    sentences = [lexicon.gen_topic(n_sentences // 5 + 2)]

    for i in range(n_sentences):
        sentences.append(gen_sentence(lexicon)[0])
        lexicon.forget_sentence_history()

    full_text = ""
    start_with_space = False

    for sentence in sentences:
        if start_with_space:
            full_text += " "

        full_text += clean_sentence(sentence)
        start_with_space = True

        if break_into_paragraphs and not random.randint(0, 5):
            full_text += "\n"
            start_with_space = False

    return full_text.strip()
