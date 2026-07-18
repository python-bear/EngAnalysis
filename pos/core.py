import os
from functools import lru_cache

import nltk
import pickle
import string
import random

from collections import defaultdict

import util
import wiki
from pos.wikitionary_inference import get_wiktionary_pos
from pos.local_inference import infer_poss


nltk.download('punkt_tab')

NLTK_TO_WIKI_POS_TAGS = {
    "$": "noun",  # dollar
    "''": None,  # closing quotation mark
    "(": None,  # opening parenthesis
    ")": None,  # closing parenthesis
    ",": None,  # comma
    "--": None,  # dash
    ".": None,  # sentence terminator
    ":": None,  # colon or ellipsis
    "CC": "conjunction",  # conjunction, coordinating
    "CD": "numeral",  # numeral, cardinal
    "DT": "determiner",  # determiner
    "EX": "pronoun",  # existential there
    "FW": "noun",  # foreign word
    "IN": "preposition",  # preposition or conjunction, subordinating
    "JJ": "adjective",  # adjective or numeral, ordinal
    "JJR": "adjective",  # adjective, comparative
    "JJS": "adjective",  # adjective, superlative
    "LS": "adjective",  # list item marker
    "MD": None,  # modal auxiliary
    "NN": "noun",  # noun, common, singular or mass
    "NNP": "proper noun",  # noun, proper, singular
    "NNPS": "proper noun",  # noun, proper, plural
    "NNS": "noun",  # noun, common, plural
    "PDT": "determiner",  # pre-determiner
    "POS": None,  # genitive marker
    "PRP": "pronoun",  # pronoun, personal
    "PRP$": "pronoun",  # pronoun, possessive
    "RB": "adverb",  # adverb
    "RBR": "adverb",  # adverb, comparative
    "RBS": "adverb",  # adverb, superlative
    "RP": "preposition",  # particle
    "SYM": "symbol",  # symbol
    "TO": "preposition",  # "to" as preposition or infinitive marker
    "UH": "interjection",  # interjection
    "VB": "verb",  # verb, base form
    "VBD": "verb",  # verb, past tense
    "VBG": "verb",  # verb, present participle or gerund
    "VBN": "verb",  # verb, past participle
    "VBP": "verb",  # verb, present tense, not 3rd person singular
    "VBZ": "verb",  # verb, present tense, 3rd person singular
    "WDT": "determiner",  # WH-determiner
    "WP": "pronoun",  # WH-pronoun
    "WP$": "pronoun",  # WH-pronoun, possessive
    "WRB": "adverb",  # Wh-adverb
    "``": None,  # opening quotation mark
}

POPULAR_PAGES_PATH = "popular_wiki_sentences.pkl"
POPULAR_PAGE_TITLES = (
    "Philosophy", "Science", "Society", "Technology", "Mathematics", "Life", "Black hole", "Mars", "Evolution",
    "Potato", "Cthulhu", "World War II", "United Kingdom", "Australia", "China", "Chernobyl disaster", "Earth",
    "William Shakespeare"
)
popular_sentences = None


def remove_chars(text: str, unwanted_chars: str) -> str:
    for char in unwanted_chars:
        text = text.replace(char, "")

    return text


def extract_sentences() -> list:
    clean_sentences = []

    for title in POPULAR_PAGE_TITLES:
        data = wiki.request_wikipedia_json(title)
        content = " ".join(next(iter(data["query"]["pages"].values()))["extract"].split())

        for unwanted_section in (
                "== References ==", "== See also ==", "== Notes ==", "== Further reading ==", "== External links =="
        ):
            if unwanted_section in content:
                content = content[:content.index(unwanted_section)]

        for sentence_ender in ".?!":
            content.replace(f"{sentence_ender} ", sentence_ender)

        sentence_ends = [i for i, char in enumerate(content) if char in (".", "?", "!")]
        sentences = [content[i + 2:j + 1] for i, j in zip([-2] + sentence_ends[:-1], sentence_ends)]

        for i, sentence in enumerate(sentences):
            try:
                if (len(sentence) < 8
                        or len(sentences[i + 1]) < 5
                        or len(sentence) > 190
                        or sentence.count(" ") > 15
                        or sentence[0] not in string.ascii_uppercase):
                    continue

            except IndexError:
                pass

            for char in sentence:
                if char not in string.ascii_lowercase + string.ascii_uppercase + " -,.?!()":
                    break

            else:
                clean_sentences.append(sentence)

    return clean_sentences


if os.path.exists(POPULAR_PAGES_PATH):
    with open(POPULAR_PAGES_PATH, "rb") as file:
        popular_sentences = pickle.load(file)

else:
    popular_sentences = extract_sentences()

    with open(POPULAR_PAGES_PATH, "wb") as file:
        pickle.dump(popular_sentences, file)


@lru_cache(maxsize=8000)
def get_poss(word: str, printable: bool = True):
    poss = get_wiktionary_pos(word)

    if poss:
        poss = {pos: 1 for pos in poss}

    else:
        poss = infer_poss(word)

    if printable:
        levels = defaultdict(list)

        for key, value in poss.items():
            levels[value].append(key)

        levels = [levels[key] for key in sorted(levels, reverse=True)]

        return "; ".join(", ".join(p for p in level) for level in levels), poss

    else:
        return poss


def contextify_word(word, pos, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        sentence = random.choice(popular_sentences)

        pos_tagged_sentence = [
            (word, NLTK_TO_WIKI_POS_TAGS[pos]) for (word, pos) in nltk.pos_tag(nltk.word_tokenize(sentence))
        ]

        sentence_words_of_pos = [
            word for word, pos_ in pos_tagged_sentence if pos_ == pos and word != "example"
        ]

        if sentence_words_of_pos:
            word_to_replace = random.choice(sentence_words_of_pos)
            i_to_replace = random.choice(list(util.find_all_substrings(sentence, word_to_replace)))

            if i_to_replace == 0:
                word = word.capitalize()

            return sentence[:i_to_replace] + word + sentence[i_to_replace + len(word_to_replace):]

    if pos == "interjection":
        return f"Oh {word}!"

    raise TimeoutError(f"Could not contextify_word for {word=} and {pos=}, reached {max_attempts=}")
