import os.path as path
import colorama

from functools import lru_cache


colorama.init(autoreset=False)

SUBSTRING_DB_FILE = "scraped/substring_data.db"
WORD_DB_FILE = "scraped/word_data.db"
PHONETIC_DB_FILE = "scraped/phonetic_data.db"


class Words:
    def __init__(self, source: str):
        self.path = path.join(source, "words.txt")
        self._len = sum(1 for _ in open(self.path, "r", encoding="utf8"))

    def __len__(self):
        return self._len

    def __iter__(self):
        with open(self.path, "r", encoding="utf8") as words_file:
            for line in words_file:
                match line.split(" "):
                    case [word, freq_count]:
                        yield word, int(freq_count)

                    case _:
                        yield line, 1


@lru_cache(maxsize=50000)
def find_all_substrings(text, sub):
    """Yields indexes of all occurrences of sub in text"""
    start = 0

    while True:
        start = text.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)


def segment_ipa(ipa_txt):
    segments = []
    i = 0
    while i < len(ipa_txt):
        if i + 1 < len(ipa_txt) and ipa_txt[i + 1] in {"ː", "ˑ"}:
            segments.append(ipa_txt[i] + ipa_txt[i + 1])
            i += 2
        else:
            segments.append(ipa_txt[i])
            i += 1

    return tuple(segments)


@lru_cache(maxsize=100000)
def get_substrings(word):
    result = set()
    for i in range(len(word)):
        for j in range(i + 1, len(word) + 1):
            result.add(word[i:j])
    return result


@lru_cache(maxsize=100000)
def get_ipa_substrings(segmented_ipa):
    result = set()
    for i in range(len(segmented_ipa)):
        for j in range(i + 1, len(segmented_ipa) + 1):
            result.add("".join(segmented_ipa[i:j]))
    return result
