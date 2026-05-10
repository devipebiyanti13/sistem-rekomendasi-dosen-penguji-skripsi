import numpy as np

def hitung_jumlah_relevan(
    rekomendasi,
    ground_truth,
    k
):
    top_k = rekomendasi[:k]
    jumlah = 0
    for dosen in top_k:
        if dosen in ground_truth:
            jumlah += 1

    return jumlah

# ================= PRECISION@K =================

def precision_at_k(
    rekomendasi,
    ground_truth,
    k
):
    jumlah_relevan = hitung_jumlah_relevan(
        rekomendasi,
        ground_truth,
        k
    )

    precision = jumlah_relevan / k
    return precision


# ================= RECALL@K =================

def recall_at_k(
    rekomendasi,
    ground_truth,
    k
):
    jumlah_relevan = hitung_jumlah_relevan(
        rekomendasi,
        ground_truth,
        k
    )
    if len(ground_truth) == 0:
        return 0

    recall = jumlah_relevan / len(ground_truth)
    return recall


# ================= DCG =================

def dcg_at_k(
    rekomendasi,
    ground_truth,
    k
):
    dcg = 0
    top_k = rekomendasi[:k]
    for i, dosen in enumerate(top_k):
        if dosen in ground_truth:
            rel = 1
        else:
            rel = 0
        dcg += (2**rel - 1) / np.log2(i + 2)

    return dcg


# ================= IDCG =================

def idcg_at_k(
    ground_truth,
    k
):
    ideal_length = min(
        len(ground_truth),
        k
    )
    idcg = 0
    for i in range(ideal_length):
        rel = 1
        idcg += (2**rel - 1) / np.log2(i + 2)

    return idcg


# ================= NDCG =================

def ndcg_at_k(
    rekomendasi,
    ground_truth,
    k
):
    dcg = dcg_at_k(
        rekomendasi,
        ground_truth,
        k
    )

    idcg = idcg_at_k(
        ground_truth,
        k
    )

    if idcg == 0:
        return 0
    ndcg = dcg / idcg
    return ndcg


# ================= SEMUA METRIK =================

def hitung_metrik(
    rekomendasi,
    ground_truth,
    k=10
):
    precision = precision_at_k(
        rekomendasi,
        ground_truth,
        k
    )

    recall = recall_at_k(
        rekomendasi,
        ground_truth,
        k
    )

    ndcg = ndcg_at_k(
        rekomendasi,
        ground_truth,
        k
    )

    return precision, recall, ndcg