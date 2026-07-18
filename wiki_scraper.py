import sys
import warnings
import wikipedia
import sqlite3
import pickle
import os
import time
import threading
import eng_to_ipa as ipa
import tkinter as tk
from tkinter import ttk
from collections import defaultdict

from alive_progress import alive_bar
from bs4 import GuessedAtParserWarning
from colorama import Fore, Style

from util import *


colorama.init(autoreset=False)  # Do not change to True
warnings.filterwarnings("ignore", category=GuessedAtParserWarning)
wikipedia.set_lang("en")

S_BLINK = "\033[5m"
F_BLINK = "\033[6m"
SLEEP_TIME = 0
HISTORY_FILE = "scraped/history.pkl"


def trace(string: str, colors: tuple[str, ...] = tuple()):
    i = 0
    prev_char = None

    for char in string:
        if char.isspace():
            print(char, end="")
        else:
            time.sleep(SLEEP_TIME)

            if i < len(colors):
                print(colors[i] + char, end="", flush=True)
            else:
                print(char, end="", flush=True)

            if char == "─" and prev_char == "│":
                i += 1
            elif char != "─":
                i += 1
        prev_char = char


def traced_bar_prefix(text, colors):
    result = ""
    i = 0
    prev_char = None
    for char in text:
        if char.isspace():
            result += char
        else:
            color = colors[i] if i < len(colors) else ""
            result += f"{color}{char}"
            if char == "─" and prev_char == "│":
                i += 1
            elif char != "─":
                i += 1
        prev_char = char
    return result + Style.RESET_ALL


def title(string: str, color: str):
    print(f"{Style.BRIGHT}{color}[", end="")
    trace(string)
    print(f"]{Style.RESET_ALL}")


def ellipses():
    time.sleep(SLEEP_TIME)
    print(f"{F_BLINK}.", end="", flush=True)
    time.sleep(SLEEP_TIME)
    print(f"{S_BLINK}.", end="", flush=True)
    time.sleep(SLEEP_TIME)
    print(f"{F_BLINK}. {Style.RESET_ALL}", end="", flush=True)
    time.sleep(SLEEP_TIME)


# Load visited titles history
visited_titles = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "rb") as file:
        visited_titles = pickle.load(file)
else:
    with open(HISTORY_FILE, "wb") as file:
        pickle.dump(visited_titles, file)


def init_db():
    # Initialize substring database
    conn = sqlite3.connect(SUBSTRING_DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS substrings (
            substring TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

    # Initialize word database
    conn = sqlite3.connect(WORD_DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

    # Initialize phonetics database
    conn = sqlite3.connect(PHONETIC_DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phonetics (
            phonetic TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def save_history():
    with open(HISTORY_FILE, "wb") as h_file:
        pickle.dump(visited_titles, h_file)


def update_count(table, value):
    match table:
        case "words":
            db_file = WORD_DB_FILE
        case "phonetics":
            db_file = PHONETIC_DB_FILE
        case "substrings":
            db_file = SUBSTRING_DB_FILE
        case _:
            raise AttributeError("db_file was None")

    conn = sqlite3.connect(db_file, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO " + table + " (" + table[:-1] + ", count) VALUES (?, 1) ON CONFLICT(" + table[:-1]
        + ") DO UPDATE SET count = count + 1",
        (value,)
    )
    conn.commit()
    conn.close()


def get_random_page():
    trace(" │││├┬", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET, Fore.BLUE))
    title("Finding Page", Fore.BLUE)

    while True:
        wiki_title = wikipedia.random()

        if wiki_title not in visited_titles:
            visited_titles.add(wiki_title)
            try:
                page = wikipedia.page(wiki_title, auto_suggest=False)
                trace(" ││││└─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET, Fore.BLUE))
                print(f"{Fore.GREEN}SUCCESS: {Fore.BLUE}{wiki_title}")
                return page.content
            except wikipedia.DisambiguationError:
                trace(" ││││├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET, Fore.BLUE))
                print(f"{Fore.RED}FAILURE: {Fore.BLUE}DisambiguationError")
                continue
            except wikipedia.PageError:
                trace(" ││││├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET, Fore.BLUE))
                print(f"{Fore.RED}FAILURE: {Fore.BLUE}PageError")
                continue
        else:
            trace(" ││││├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET, Fore.BLUE))
            print(f"{Fore.RED}FAILURE: {Fore.BLUE}Page already in history")


def process_text(text):
    word_counts = defaultdict(int)
    substring_counts = defaultdict(int)
    phonetic_counts = defaultdict(int)

    words = text.lower().strip().replace("\n", " ").replace("\t", " ").replace("\r", " ").split(" ")
    words = [word for word in words if not word.isspace() and len(word) > 0]

    prefix = traced_bar_prefix(" │││├ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET))

    with alive_bar(len(words), bar="smooth", spinner="waves", title=prefix + "Processing", length=10) as bar:
        for word in words:
            word_counts[word] += 1
            for sub in get_substrings(word):
                substring_counts[sub] += 1

            if ipa.isin_cmu(word):
                ipa_txt = ipa.convert(word, False, True).lstrip("ˈ").replace("ˌ", "").replace("ˈ", "")
                segmented_ipa = segment_ipa(ipa_txt)
                for ps in get_ipa_substrings(segmented_ipa):
                    phonetic_counts[ps] += 1
            bar()

    trace(" │├│─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTMAGENTA_EX))
    trace("Updating Database")
    ellipses()

    bulk_db_update("words", word_counts)
    bulk_db_update("substrings", substring_counts)
    bulk_db_update("phonetics", phonetic_counts)
    print(f"{Fore.GREEN}SUCCESS")

def bulk_db_update(table, counts):
    db_file = {
        "words": WORD_DB_FILE,
        "substrings": SUBSTRING_DB_FILE,
        "phonetics": PHONETIC_DB_FILE
    }[table]

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION")
    for value, count in counts.items():
        cursor.execute(f"""
            INSERT INTO {table} ({table[:-1]}, count)
            VALUES (?, ?)
            ON CONFLICT({table[:-1]}) DO UPDATE SET count = count + ?
        """, (value, count, count))
    conn.commit()
    conn.close()


def get_all_substrings(table: str):
    data_name = "word" if table == WORD_DB_FILE else "phonetic" if table == PHONETIC_DB_FILE else "substring" \
        if table == SUBSTRING_DB_FILE else None

    conn = sqlite3.connect(table, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT {data_name}, count 
        FROM {data_name}s 
        WHERE "count" >= 10
        ORDER BY count DESC
    """)
    substrings = cursor.fetchall()
    conn.close()
    return substrings


class SubstringApp:
    def __init__(self, root):
        self.table_path = SUBSTRING_DB_FILE

        self.root = root
        self.root.title(f"[English-Wiki-Analysis]- {SUBSTRING_DB_FILE}")
        self.root.geometry("600x400")

        self.root_frame = tk.Frame(root)
        self.root_frame.columnconfigure(0, weight=1)
        self.root_frame.columnconfigure(1, weight=0)
        self.root_frame.rowconfigure(0, weight=1)
        self.root_frame.rowconfigure(1, weight=0)
        self.root_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.root_frame, columns=("Index", "Substring", "Length", "Count", "Percentage"), show="headings"
        )

        # Configure columns
        self.tree.heading("Index", text="Index")
        self.tree.heading("Substring", text="Substring")
        self.tree.heading("Length", text="Length")
        self.tree.heading("Count", text="Count")
        self.tree.heading("Percentage", text="Percentage")

        # Set column widths
        self.tree.column("Index", width=50, anchor="center")
        self.tree.column("Substring", width=150, anchor="center")
        self.tree.column("Length", width=50, anchor="center")
        self.tree.column("Count", width=100, anchor="center")
        self.tree.column("Percentage", width=150, anchor="center")

        self.tree.grid(row=0, column=0, sticky="NESW")

        self.scrollbar = ttk.Scrollbar(self.root_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS)

        self.action_frame = tk.Frame(self.root_frame)
        self.action_frame.columnconfigure(0, weight=1)
        self.action_frame.columnconfigure(1, weight=1)
        self.action_frame.columnconfigure(2, weight=1)
        self.action_frame.columnconfigure(3, weight=1)
        self.action_frame.columnconfigure(4, weight=1)
        self.action_frame.rowconfigure(1, weight=1)
        self.action_frame.rowconfigure(2, weight=1)
        self.action_frame.grid(row=1, column=0, sticky="NESW", padx=15, pady=20)

        self.update_button = ttk.Button(self.action_frame, text="Update", command=self.update_data)
        self.update_button.grid(row=0, column=0, sticky="NESW")

        self.update_button = ttk.Button(
            self.action_frame, text="Substring", command=lambda x=SUBSTRING_DB_FILE: self.change_source(x)
        )
        self.update_button.grid(row=0, column=1, sticky="NESW")

        self.update_button = ttk.Button(
            self.action_frame, text="Word", command=lambda x=WORD_DB_FILE: self.change_source(x)
        )
        self.update_button.grid(row=1, column=0, sticky="NESW")

        self.update_button = ttk.Button(
            self.action_frame, text="Phonetic", command=lambda x=PHONETIC_DB_FILE: self.change_source(x)
        )
        self.update_button.grid(row=1, column=1, sticky="NESW")

        self.goto_label = ttk.Label(self.action_frame, text="Find:")
        self.goto_label.grid(row=0, column=2, sticky="NESW")
        self.goto_entry = ttk.Entry(self.action_frame)
        self.goto_entry.grid(row=0, column=3, sticky="NESW")
        self.goto_button = ttk.Button(self.action_frame, text="Search", command=self.goto_substring)
        self.goto_button.grid(row=1, column=2, sticky="NESW", columnspan=2)

        self.total_label = ttk.Label(self.action_frame, text="Substrings:\n 0")
        self.total_label.grid(row=0, column=4, sticky="NESW", rowspan=2)

        self.update_data()

    def change_source(self, new_table_path: str):
        self.table_path = new_table_path
        self.update_data()
        self.root.title(f"Eng Analysis: {new_table_path}")

    def update_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        substrings = get_all_substrings(self.table_path)
        total_count = sum(count for _, count in substrings)
        self.total_label.config(text=f"Substrings:\n {total_count}")

        for idx, (substring, count) in enumerate(substrings, start=1):
            length = len(substring)
            percentage = (count / total_count) * 100 if total_count > 0 else 0

            self.tree.insert("", "end", values=(idx, substring, length, count, f"{percentage:.8f}%"))

    def goto_substring(self):
        search_text = self.goto_entry.get()
        for row in self.tree.get_children():
            values = self.tree.item(row, "values")
            if values and values[1] == search_text:  # Change index to match 'Substring' column
                self.tree.selection_set(row)
                self.tree.see(row)
                break


def scraping_thread(stop_event):
    i = 0
    while not stop_event.is_set():
        trace(" ││├┬", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET))
        title("Scraping Page", Fore.RESET)
        page_text = get_random_page()

        process_text(page_text)

        trace(" │││└ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RESET))
        print(f"{Fore.YELLOW}COMPLETED{Fore.RESET} ({i + 1} pages since startup)")
        i += 1

    trace(" ││└ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX))
    print(f"{Fore.YELLOW}COMPLETED{Fore.RESET}")


def fail_exit(stage: str, error: Exception):
    print(f"{Fore.RED}FAILURE - {stage}")
    print(f"\n{Fore.RED}{error}")
    sys.exit()


def on_closing():
    root.destroy()
    shutdown_event.set()
    scraper_thread.join()

    trace(" │├ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX))
    trace("Saving History")
    ellipses()
    save_history()
    print(f"{Fore.GREEN}SUCCESS")

    trace(" │└ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX))
    print(f"{Fore.YELLOW}COMPLETED{Fore.RESET}")

    trace(" └ ", (Fore.LIGHTYELLOW_EX,))
    trace("Terminated\n")


if __name__ == "__main__":
    title("English-Wiki-Analysis", Fore.LIGHTYELLOW_EX)
    trace(" ├┬", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX))
    title("Database", Fore.LIGHTMAGENTA_EX)
    trace(" │├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX))
    trace("Connecting")
    ellipses()

    try:
        init_db()
        print(f"{Fore.GREEN}SUCCESS")
    except Exception as e:
        fail_exit("initializing database", e)

    trace(" ├─┬", (Fore.LIGHTYELLOW_EX, Fore.LIGHTRED_EX))
    title("Scraper Thread", Fore.LIGHTRED_EX)
    trace(" ││├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX))
    trace("Defined\n")
    trace(" ││├─ ", (Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX))
    trace("Starting")
    ellipses()

    try:
        shutdown_event = threading.Event()
        scraper_thread = threading.Thread(
            target=scraping_thread,
            args=(shutdown_event,),
            daemon=True
        )
        print(f"{Fore.GREEN}SUCCESS")

    except Exception as e:
        fail_exit("starting scraping thread", e)
        sys.exit()

    scraper_thread.start()

    root = tk.Tk()
    app = SubstringApp(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()
