import wiki
import mwparserfromhell


PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection",
    "definitions", "pronoun",
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "coordinate terms",
]


def get_wiktionary_pos(word: str) -> set:
    data = wiki.request_wiktionary_json(word)

    pages = data["query"]["pages"]
    if "missing" in pages[0]:
        return set()

    if pages[0].get("invalid", False):
        raise ValueError(pages[0])

    text = pages[0]["revisions"][0]["content"]
    wikicode = mwparserfromhell.parse(text)

    pos = set()
    lang = None

    for section in wikicode.get_sections(include_lead=False):
        headings = section.filter_headings()
        if not headings:
            continue

        h = headings[0]
        title = h.title.strip_code().strip().lower()

        if h.level == 2:
            lang = title

        elif lang == "english" and title in PARTS_OF_SPEECH:
            pos.add(title)

    return pos
