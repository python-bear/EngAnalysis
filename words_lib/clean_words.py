import unicodedata

from tqdm import tqdm
from os import path


ACCENTS = ["̀", "́", "̂", "̈", "̋", "̌"]
ALLOWABLE_CHARS = list("abcdefghijklmnopqrstuvwxyzæç'-") + ACCENTS
BAD_QUOTES = (
    "’", "‘", "‚", "‛",   # single quotes
    "“", "”", "„", "‟",   # double quotes
    "′", "‵",              # primes
    "ʼ", "ʽ", "ʾ", "ʿ",   # modifier letter apostrophes
    "＇", "＂"             # fullwidth
)


def decompose_baked_accents(text: str) -> str:
    return unicodedata.normalize("NFD", text)


with open("obscure_words.txt", "r", encoding="utf8") as in_file:
    with open(path.join("big", "words.txt"), "a", encoding="utf8") as out_file:
        lines = sum(1 for _ in in_file)
        in_file.seek(0)

        for line in tqdm(in_file, total=lines):
            line = line.lower().strip()
            clean_line = ""

            for char in line:
                if char in ALLOWABLE_CHARS:
                    clean_line += char

                elif char in " —~‑‒―⁓−⸺⸻":
                    clean_line += "-"

                elif char in BAD_QUOTES:
                    clean_line += "'"

                else:
                    d_char = decompose_baked_accents(char)

                    if len(d_char) > len(char):
                        if any(accent in d_char for accent in ACCENTS):
                            clean_line += d_char

                        else:
                            clean_line += d_char[0]

                    else:
                        clean_line = False
                        break

            if clean_line:
                out_file.write(f"{clean_line}\n")
