import re

def preprocess_bidang(text):

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = re.sub(r"[\"()]", " ", text)

    text = text.replace("/", " ")

    text = re.sub(r"[^a-zA-Z\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

def tambah_sinonim(text):

    synonyms = {
        "pengolahan citra": "image processing",
        "sistem pendukung keputusan": "decision support system",
        "kecerdasan buatan": "artificial intelligence",
        "rekayasa perangkat lunak": "software engineering"
    }

    for indo, eng in synonyms.items():
        text = text.replace(indo, eng)

    return text