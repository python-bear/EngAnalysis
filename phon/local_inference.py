import nltk
nltk.download('averaged_perceptron_tagger_eng')

from g2p_en import G2p


ARPABET_TO_IPA = {
    "AA": "ɑ~ɒ",
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔ",
    "AW": "a͡ʊ",
    "AX": "ə",
    "AXR": "ɚ",
    "AY": "a͡ɪ",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "e͡ɪ",
    "IH": "ɪ",
    "IX": "ɨ",
    "IY": "i",
    "OW": "o͡ʊ",
    "OY": "ɔ͡ɪ",
    "UH": "ʊ",
    "UW": "u",
    "UX": "ʉ",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "DX": "ɾ",
    "EL": "l̩",
    "EM": "m̩",
    "EN": "n̩",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "H": "h",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NX": "ŋ",
    "NG": "ŋ",
    "NX": "ɾ̃",
    "P": "p",
    "Q": "ʔ",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "V": "v",
    "W": "w",
    "WH": "ʍ",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}


def arpabet_to_ipa(arpabet: list) -> str:
    ipa = ""

    for phoneme in arpabet:
        if "0" in phoneme:
            phoneme = phoneme.strip("0")

        elif "1" in phoneme:
            ipa += "ˈ"
            phoneme = phoneme.strip("1")

        elif "2" in phoneme:
            ipa += "ˌ"
            phoneme = phoneme.strip("2")

        ipa += ARPABET_TO_IPA[phoneme]

    return ipa


if __name__ == "__main__":
    texts = (
        "hypophosphatide", "snarlicking", "tiller", "secrecies", "shed", "hexaf", "photoionizing", "quies", "noncle"
    )

    g2p = G2p()

    for text in texts:
        out = g2p(text)
        print(f"{arpabet_to_ipa(out)} : {' '.join(out)}")
