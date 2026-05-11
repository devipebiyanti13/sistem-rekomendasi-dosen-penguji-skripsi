import psycopg2
from langdetect import detect
from deep_translator import GoogleTranslator
import time
import re
import nltk
import streamlit as st
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# ================= KONEKSI =================
conn = psycopg2.connect(
    st.secrets["DATABASE_URL"]
)
cur = conn.cursor()

# ================= DETEKSI BAHASA =================
def detect_lang(text):
    try:
        return detect(text)
    except:
        return "unknown"

# ================= TRANSLATE =================
def translate_to_indonesia(text, lang):
    try:
        if lang == "en":
            return GoogleTranslator(source="auto", target="id").translate(text)
        else:
            return text
    except:
        return text

# ================= PREPROCESS =================
nltk.download('punkt')
nltk.download('stopwords')

factory = StemmerFactory()
stemmer = factory.create_stemmer()
stop_words = set(stopwords.words('indonesian'))

normalization_dict = {
    "svm": "support vector machine",
    "knn": "k nearest neighbor",
    "kmeans": "k means",
    "cnn": "convolutional neural network",
    "lda": "latent dirichlet allocation",
    "ahp": "analytic hierarchy process",
    "fahp": "fuzzy analytic hierarchy process",
    "topsis": "topsis",
    "copras": "copras",
    "smo": "sequential minimal optimization",
    "iot": "internet of things",
    "vr": "virtual reality",
    "nlp": "natural language proccesing",
}

def split_stuck_words(text):
    common_words = [
        "menggunakan", "dengan", "dan", "pada", "untuk",
        "data", "model", "analisis", "algorithm", "optimization",
        "clustering", "particle", "swarm", "genetic", "automatic"
    ]
    for w in common_words:
        text = re.sub(rf"(?i)(\w)({w})", r"\1 \2", text)
        text = re.sub(rf"(?i)({w})(\w)", r"\1 \2", text)
    return text

def preprocess_text(text):
    if not isinstance(text, str):
        return ""

    text = split_stuck_words(text)
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()

    # normalization
    normalized_tokens = []
    for t in tokens:
        if t in normalization_dict:
            normalized_tokens.extend(normalization_dict[t].split())
        else:
            normalized_tokens.append(t)

    tokens = normalized_tokens

    # stopword removal
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

    # stemming
    tokens = [stemmer.stem(t) for t in tokens]

    return " ".join(tokens)

# ================= AMBIL DATA =================
cur.execute("""
    SELECT id_dosen, bidang_minat
    FROM dosen
    WHERE bidang_minat_preprocessed IS NULL
""")

data = cur.fetchall()

print(f"Total data bidang minat: {len(data)}")

# ================= LOOP =================
for i, row in enumerate(data):
    id_dosen = row[0]
    bidang_minat = row[1]

    try:
        bahasa = detect_lang(bidang_minat)

        bidang_translate = translate_to_indonesia(bidang_minat, bahasa)

        bidang_preprocessed = preprocess_text(bidang_translate)

        cur.execute("""
            UPDATE dosen
            SET bahasa_bidang_minat = %s,
                bidang_minat_translate = %s,
                bidang_minat_preprocessed = %s
            WHERE id_dosen = %s
        """, (bahasa, bidang_translate, bidang_preprocessed, id_dosen))

        print(f"{i+1}/{len(data)} - Berhasil ID {id_dosen}")

        time.sleep(0.3)

    except Exception as e:
        print(f"Error di ID {id_dosen}: {e}")

# ================= SIMPAN =================
conn.commit()
conn.close()

print("Preprocessing bidang minat selesai!")