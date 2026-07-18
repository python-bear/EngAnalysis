from collections import defaultdict


PREFIXES = {
    "noun": (
        "non", "un", "re", "co", "sub", "inter", "intra", "after", "back", "a", "an", "ana", "anti", "contra", "contro",
        "counter", "mal", "pseudo", "bi", "di", "duo", "du", "quadri", "tri", "mono", "uni", "multi", "mult", "semi",
        "demi", "maxi", "micro", "macro", "megalo", "ultra", "ante", "pre", "post", "retro", "preter", "proto",
        "deuter", "afro", "anglo", "franco", "euro", "hispano", "indo", "italo", "astro", "geo", "hydro", "photo",
        "electro", "cryo", "pyro", "gyro", "iso", "ortho", "paleo", "ped", "pod", "pleo", "socio", "ideo", "idio",
        "hetero", "homo", "hypo", "hyper", "eco", "circum", "peri", "trans", "tele", "pro", "pros", "ob", "para", "syn",
        "sy", "syl", "sym", "arch", "super", "supra", "ultra", "omni", "extra", "maxi", "mega", "megal", "vice", "ideo",
        "idio", "gyro", "cryo", "crypto", "cryp", "deuter", "hetero", "homo", "ped", "pod"
    ),
    "verb": (
        "re", "dis", "de", "pre", "post", "mis", "en", "a", "be", "dis", "di", "dif", "circum", "peri", "trans", "tele",
        "pro", "pros", "ob", "para", "syn", "sy", "syl", "sym"
    ),
    "adjective": (
        "un", "in", "im", "il", "ir", "anti", "contra", "counter", "a", "an", "ana", "anti", "contra", "contro",
        "counter", "de", "dis", "di", "dif", "non", "mal", "pseudo", "bi", "duo", "du", "quadri", "tri", "mono", "uni",
        "multi", "mult", "semi", "demi", "maxi", "micro", "macro", "megalo", "ultra", "ante", "pre", "post", "retro",
        "preter", "proto", "deuter", "epi", "meta", "inter", "intra", "trans", "tele", "infra", "supra", "super", "sub",
        "sur", "afro", "anglo", "franco", "euro", "hispano", "indo", "italo", "astro", "geo", "hydro", "photo",
        "electro", "cryo", "pyro", "gyro", "iso", "ortho", "paleo", "ped", "pod", "pleo", "socio", "ideo", "idio",
        "hetero", "homo", "hypo", "hyper", "eco", "circum", "peri", "trans", "tele", "pro", "pros", "ob", "para", "syn",
        "sy", "syl", "sym", "arch", "super", "supra", "ultra", "omni", "extra", "maxi", "mega", "megal", "cryo",
        "crypto", "cryp", "hetero", "homo", "ped", "pod"
    ),
    "adverb": (
        "non", "pre", "post", "epi", "meta", "inter", "intra", "trans", "tele", "infra", "supra", "super", "sub", "sur"
    ),
}

for key, val in PREFIXES.items():
    PREFIXES[key] = sorted(val, key=len, reverse=True)

SUFFIXES = {
    "noun": (
        "ment", "ness", "tion", "sion", "ity", "ence", "ance", "hood", "ship", "dom", "er", "or", "ism", "ist", "ion",
        "gh", "rum", "ds", "cy"
    ),
    "present verb": ("ate", "ify", "ise", "ize", "en"),
    "past verb": ("ised", "ized", "ed"),
    "adjective": ("able", "ible", "al", "ful", "ic", "ive", "ous", "ish", "less", "y", "tis"),
    "adverb": ("ly", "ward", "wise")
}

for key, val in SUFFIXES.items():
    SUFFIXES[key] = sorted(val, key=len, reverse=True)

VOWELS = ("a", "e", "i", "o", "u", "y")


def strip_vowel(text: str) -> str:
    for vowel in VOWELS:
        text = text.rstrip(vowel)

    return text


def infer_poss(word: str) -> dict:
    word = word.lower()

    poss = defaultdict(int)

    for pos, ends in SUFFIXES.items():
        if any(word.endswith(e) for e in ends):
            poss[pos] += 1

    if not poss:
        for s_ending in ("s", "es"):
            if word.endswith(s_ending):
                if word[:-len(s_ending)].endswith("el"):
                    poss["noun"] += 1
                    break

                found = False

                for pos in ("noun", "present verb"):
                    if any(word[:-len(s_ending)].endswith(e) for e in SUFFIXES[pos]):
                        poss[pos] += 1
                        found = True

                if not found:
                    poss["noun"] += 1
                    poss["verb"] += 1

    if not poss:
        if word.endswith("ing"):
            if any(word[:-3].endswith(e) or word[:-3].endswith(strip_vowel(e)) for e in SUFFIXES["present verb"]):
                poss["present verb"] += 1

            else:
                poss["present verb"] += 1
                poss["noun"] += 1

        elif word.endswith("t") and word[-2] not in VOWELS:
            poss["past verb"] += 1


    if not poss:
        poss["noun"] = 1


    for pos, ends in SUFFIXES.items():
        if any(word.endswith(e) for e in ends):
            poss[pos] *= 1.5

    verb_total = poss["verb"] + poss["present verb"] + poss["past verb"]

    poss = dict(poss)

    del poss["present verb"]
    del poss["past verb"]

    if verb_total:
        poss["verb"] = verb_total

    else:
        del poss["verb"]

    return poss