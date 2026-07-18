import pickle
import sqlite3

from util import *


ALPHABET = tuple("abcdefghijklmnopqrstuvwxyz")
ENGLISH_LETTERS = set(ALPHABET)
VOWELS = ("a", "e", "i", "o", "u", "y")

START_TOKEN = "<"
END_TOKEN = ">"
SPECIAL_TOKENS = [
    # suffixes
    "er", "ly", "able", "ible", "hood", "ful", "less", "ish", "ness", "ic", "ist", "ian", "or", "eer", "logy",
    "ship", "ous", "ive", "age", "ant", "ent", "ary", "ize", "ise", "ure", "ion", "tion", "nce", "ity", "al", "ate",
    "tude", "ism", "ti",
    # prefixes
    "de", "dis", "trans", "dia", "ex", "e", "mono", "uni", "di", "tri", "multi", "poly", "pre", "post", "mal",
    "mis", "bene", "pro", "sub", "re", "inter", "intra", "co", "com", "con", "col", "be", "non", "un", "in", "im",
    "il", "ir", "a", "an", "anti", "contra", "counter", "en", "em",
    # greek
    "astr", "bi", "ge", "therm", "aut", "hom", "hydr", "micro", "macro", "phon", "scope", "graph", "phot", "tele",
    "meter", "metr", "path", "pass", "psych", "pan", "zoo", "chron", "phobia",
    # latin
    "port", "form", "tract", "rupt", "spec", "stru", "ct", "dic", "di", "flex", "flec", "cred", "aqua", "pel",
    "puls", "fac", "ject", "vert", "vers", "mis", "mit", "mort", "script", "scrib", "junct", "cide", "press",
    "spire", "grad", "gress", "cept", "capt",
    # grammar marks
    "'", "-",
    # special letters
    "æ", "ç",
    # accents
    "̀", "́", "̂", "̈", "̋", "̌"
]

DB_TABLE = "tokens"
TOKEN_COL = "token"


def generate_tokens(words: Words, source: str, reset: bool = False) -> tuple:
    db_file = path.join(source, f"{DB_TABLE}.db")

    db_missing = not path.exists(db_file)

    with sqlite3.connect(db_file, check_same_thread=False) as conn:
        if db_missing:
            init_db(conn)
            build_db(words, conn)

        if reset:
            reset_tokens(source, conn)

        tokens = load_tokens(source, conn)

    return tuple(tokens)


def init_db(conn):
    cur = conn.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE} (
            {TOKEN_COL} TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)

    conn.commit()


def build_db(words: Words, conn):
    cur = conn.cursor()

    for word, count in tqdm(words):
        for sub in get_substrings(word.strip() + " "):
            cur.execute(
                f"INSERT INTO {DB_TABLE} ({TOKEN_COL}, count) VALUES (?, ?) "
                f"ON CONFLICT({TOKEN_COL}) DO UPDATE SET count = count + excluded.count",
                (sub, count)
            )

    conn.commit()


def load_tokens(source, conn) -> list:
    tokens_path = path.join(source, "tokens.pkl")

    if not path.exists(tokens_path):
        reset_tokens(source, conn)

    with open(tokens_path, "rb") as file:
        return pickle.load(file)


def reset_tokens(source, conn):
    tokens_path = path.join(source, "tokens.pkl")
    tokens = [START_TOKEN, END_TOKEN] + SPECIAL_TOKENS

    cur = conn.cursor()
    cur.execute(f"""
        SELECT {TOKEN_COL}, count
        FROM {DB_TABLE}
        ORDER BY count DESC
    """)

    while True:
        row = cur.fetchone()
        if row is None:
            raise IndexError(f"db is not large enough to provide tokens for whole alphabet")

        token, _ = row
        if set(token).issubset(ENGLISH_LETTERS) and token not in tokens:
            tokens.append(token)

        if ENGLISH_LETTERS.issubset(tokens):
            break

    with open(tokens_path, "wb") as file:
        pickle.dump(tokens, file)
