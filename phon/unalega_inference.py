import requests


def get_ipa(word: str) -> str:
    response = requests.post(
        "https://api2.unalengua.com/ipav3",
        json = {
            "text": f"{word}",
            "lang": "en-AU",
            "mode": True
        }
    )

    return response.json()["ipa"]
