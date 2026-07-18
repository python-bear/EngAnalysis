import time
import requests


HEADERS = {
    "User-Agent": "EngAnalysisBot/0.1 (contact: pythonbear@proton.me) requests/2.32.3",
    "Accept-Encoding": "gzip",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def request(params, api: str = "https://en.wikipedia.org/w/api.php"):
    """A safe wiki page getter"""
    while True:
        response = SESSION.get(api, params=params, timeout=10)

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            time.sleep(wait)
            continue

        response.raise_for_status()
        return response


def request_wikipedia_json(title: str):
    params = {
        "action": "query",
        "format": "json",
        "titles": title.lower(),
        "prop": "extracts",
        "explaintext": True
    }

    response = request(params, "https://en.wikipedia.org/w/api.php")
    return response.json()


def request_wiktionary_json(word: str):
    params = {
        "action": "query",
        "format": "json",
        "titles": word,
        "prop": "revisions",
        "rvprop": "content",
        "formatversion": 2
    }

    response = request(params, "https://en.wiktionary.org/w/api.php")
    return response.json()
