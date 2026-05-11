import psycopg2
from langdetect import detect
from deep_translator import GoogleTranslator
import time
import re
import nltk
import streamlit as st
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

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
nltk.download('punkt_tab')
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
    "nlp": "natural language processing",
}

# ================= NORMALIZATION FUNCTION =================
def normalize_tokens(tokens):
    normalized = []
    for t in tokens:
        if t in normalization_dict:
            normalized.extend(normalization_dict[t].split())
        else:
            normalized.append(t)
    return normalized

# ================= SPLIT KATA NEMPEL =================
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

# ================= PREPROCESS QUERY (FIXED) =================
def preprocess_query(text):
    if not text or not isinstance(text, str):
        return []

    # 1. detect bahasa
    try:
        lang = detect(text)
    except:
        lang = "id"

    # 2. translate kalau english
    if lang == "en":
        try:
            text = GoogleTranslator(source="auto", target="id").translate(text)
        except:
            pass

    # 3. split kata nempel
    text = split_stuck_words(text)

    # 4. case folding
    text = text.lower()

    # 5. cleaning
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. tokenization 
    tokens = nltk.word_tokenize(text)

    # 7. normalization
    tokens = normalize_tokens(tokens)

    # 8. stopword removal
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

    # 9. stemming
    tokens = [stemmer.stem(t) for t in tokens]

    return tokens


# ================= AMBIL DATA =================
cur.execute("""
    SELECT id_penelitian, judul_penelitian 
    FROM penelitian_dosen
    WHERE judul_preprocessed IS NULL
""")

data = cur.fetchall()

print(f"Total data yang akan diproses: {len(data)}")

# ================= LOOP =================
for i, row in enumerate(data):
    id_penelitian = row[0]
    judul = row[1]  

    try:
        bahasa = detect_lang(judul)

        judul_translate = translate_to_indonesia(judul, bahasa)

        judul_preprocessed = preprocess_query(judul_translate)

        cur.execute("""
            UPDATE penelitian_dosen
            SET bahasa = %s,
                judul_translate = %s,
                judul_preprocessed = %s
            WHERE id_penelitian = %s
        """, (bahasa, judul_translate, judul_preprocessed, id_penelitian))

        print(f"{i+1}/{len(data)} - Berhasil ID {id_penelitian}")

        time.sleep(0.3) 

    except Exception as e:
        print(f"Error di ID {id_penelitian}: {e}")

# ================= SIMPAN =================
conn.commit()
conn.close()

print("Backfill selesai!")