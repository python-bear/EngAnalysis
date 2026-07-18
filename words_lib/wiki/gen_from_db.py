import sqlite3
import re

DB_FILE = r"C:\Users\owenj\PycharmProjects\EngAnalysis\scraped\word_data.db"   # change if needed
OUT_FILE = "words.txt"

alpha_re = re.compile(r"^[A-Za-z]+$")

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("SELECT word, count FROM words")

with open(OUT_FILE, "w", encoding="utf-8") as f:
    for word, count in cur.fetchall():
        if alpha_re.fullmatch(word):
            f.write(f"{word.lower()} {count}\n")

conn.close()
