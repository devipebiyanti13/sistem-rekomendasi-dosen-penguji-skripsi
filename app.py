import streamlit as st
import pandas as pd
from koneksi import get_connection

if "page" not in st.session_state:
    st.session_state.page = "login"

if "role" not in st.session_state:
    st.session_state.role = None


# ================= LOGIN =================
if st.session_state.page == "login":

    col_left, col_space, col_right = st.columns([1, 0.2, 1])

    with col_left:
        st.title("Sistem Rekomendasi Dosen Penguji")
        st.subheader("Login")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("Dosen", use_container_width=True):
                st.session_state.role = "Dosen"

        with col_btn2:
            if st.button("Mahasiswa", use_container_width=True):
                st.session_state.role = "Mahasiswa"
                st.session_state.page = "dashboard_mhs"
                st.rerun()

    with col_right:
        if st.session_state.role == "Dosen":
            st.subheader("Login Dosen")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
                if username == "dosenft" and password == "162738":
                    st.session_state.page = "dashboard_dosen"
                    st.rerun()
                else:
                    st.error("Username atau Password salah")


# ================= DASHBOARD DOSEN =================
elif st.session_state.page == "dashboard_dosen":

    st.title("Dashboard Dosen 👨‍🏫")

    menu = st.sidebar.selectbox(
        "SISTEM REKOMENDASI DOSEN PENGUJI",
        ["Beranda", "Cari Rekomendasi", "Data Dosen"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.page = "login"
        st.session_state.role = None
        st.rerun()

    if menu == "Beranda":
        st.subheader("🏠 Beranda")
        st.write("Selamat datang di sistem rekomendasi dosen penguji.")

    elif menu == "Cari Rekomendasi":
        st.subheader("🔎 Cari Rekomendasi Penguji")

        topik = st.text_input("Topik Penelitian")
        judul = st.text_input("Judul Penelitian")
        abstrak = st.text_area("Abstrak")

        if st.button("Cari"):

            # VALIDASI
            if not (judul or abstrak or topik):
                st.warning("Input tidak boleh kosong!")
                st.stop()

            # ================= LOAD PICKLE =================
            import pickle
            from backfill_judul_penelitian import preprocess_query

            with open("model_rekomendasi.pkl", "rb") as f:
                model = pickle.load(f)

            tfidf_matrix = model["tfidf_matrix"]
            vocab = model["vocab"]
            idf = model["idf"]
            names = model["nama_dosen"]

            # ================= PREPROCESS QUERY =================
            query_text = topik + " " + judul + " " + abstrak
            query_tokens = preprocess_query(query_text)

            # ================= TF QUERY =================
            from collections import Counter

            def compute_tf(tokens):
                tf_dict = {}
                counter = Counter(tokens)
                max_freq = max(counter.values())

                for word, count in counter.items():
                    tf_dict[word] = count / max_freq

                return tf_dict

            tf_query = compute_tf(query_tokens)

            # ================= TF-IDF QUERY =================
            def compute_tfidf(tf, idf):
                tfidf = {}
                for word, val in tf.items():
                    if word in idf:
                        tfidf[word] = val * idf[word]
                return tfidf

            tfidf_query = compute_tfidf(tf_query, idf)

            # ================= VECTORIZE =================
            import numpy as np

            def vectorize(tfidf_dict, vocab):
                return np.array([tfidf_dict.get(word, 0) for word in vocab])

            query_vector = vectorize(tfidf_query, vocab)

            # ================= COSINE =================
            from numpy.linalg import norm

            def cosine_similarity(vec1, vec2):
                if norm(vec1) == 0 or norm(vec2) == 0:
                    return 0
                return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

            cosine_scores = [
                cosine_similarity(query_vector, doc)
                for doc in tfidf_matrix
            ]

            # ================= JACCARD =================
            def jaccard_similarity(vec1, vec2):
                vec1_bin = vec1 > 0
                vec2_bin = vec2 > 0

                intersection = np.logical_and(vec1_bin, vec2_bin).sum()
                union = np.logical_or(vec1_bin, vec2_bin).sum()

                if union == 0:
                    return 0
                return intersection / union

            jaccard_scores = [
                jaccard_similarity(query_vector, doc)
                for doc in tfidf_matrix
            ]

            # ================= AMBIL DATA DOSEN =================
            conn = get_connection()
            df_dosen = pd.read_sql(
                "SELECT nama_dosen, prodi FROM dosen",
                conn
            )
            conn.close()

            # ================= GABUNGKAN =================
            result = pd.DataFrame({
                "nama_dosen": names,
                "cosine": cosine_scores,
                "jaccard": jaccard_scores
            })

            df_dosen["nama_dosen"] = df_dosen["nama_dosen"].str.lower().str.strip()
            result["nama_dosen"] = result["nama_dosen"].str.lower().str.strip()

            result = result.merge(df_dosen, on="nama_dosen", how="left")

            # ================= SORTING =================
            # ranking cosine
            result_cosine = result.sort_values(by="cosine", ascending=False).copy()
            result_cosine["ranking"] = range(1, len(result_cosine)+1)

            # ranking jaccard
            result_jaccard = result.sort_values(by="jaccard", ascending=False).copy()
            result_jaccard["ranking"] = range(1, len(result_jaccard)+1)

            result_cosine = result_cosine[
                ["ranking", "nama_dosen", "prodi", "cosine", "jaccard"]
            ]

            result_jaccard = result_jaccard[
                ["ranking", "nama_dosen", "prodi", "cosine", "jaccard"]
            ]

            result_cosine["cosine"] = result_cosine["cosine"].round(4)
            result_cosine["jaccard"] = result_cosine["jaccard"].round(4)

            result_jaccard["cosine"] = result_jaccard["cosine"].round(4)
            result_jaccard["jaccard"] = result_jaccard["jaccard"].round(4)

            st.session_state["result_cosine"] = result_cosine
            st.session_state["result_jaccard"] = result_jaccard

        # ================= CEK HASIL =================

        if "result_cosine" in st.session_state:

            result_cosine = st.session_state["result_cosine"]
            result_jaccard = st.session_state["result_jaccard"]

            # ================= FILTER PRODI =================
            st.subheader("🎯 Filter Prodi")

            list_prodi = result_cosine["prodi"].dropna().unique().tolist()
            filter_options = ["Semua Prodi"] + sorted(list_prodi)

            selected_prodi = st.selectbox("Pilih Prodi:", filter_options)

            if selected_prodi == "Semua Prodi":
                st.info("Menampilkan semua prodi.")
                
                cosine_filtered = result_cosine.copy()
                jaccard_filtered = result_jaccard.copy()

            else:
                st.info(f"Menampilkan prodi: {selected_prodi}")
                
                cosine_filtered = result_cosine[
                    result_cosine["prodi"] == selected_prodi
                ].copy()

                jaccard_filtered = result_jaccard[
                    result_jaccard["prodi"] == selected_prodi
                ].copy()

            # reset ranking ulang
            cosine_filtered["ranking"] = range(1, len(cosine_filtered) + 1)
            jaccard_filtered["ranking"] = range(1, len(jaccard_filtered) + 1)

            # ================= TAMPILKAN =================
            st.subheader("📊 Top 10 Rekomendasi Dosen Penguji")

            st.markdown("### Cosine Similarity")
            st.dataframe(cosine_filtered.head(10), use_container_width=True)

            st.markdown("### Jaccard Similarity")
            st.dataframe(jaccard_filtered.head(10), use_container_width=True)

            if len(cosine_filtered) > 0 and len(jaccard_filtered) > 0:

                rekomendasi_cosine = cosine_filtered["nama_dosen"].head(10).tolist()
                rekomendasi_jaccard = jaccard_filtered["nama_dosen"].head(10).tolist()

                st.success(
                    f"Rekomendasi terbaik (Cosine): {cosine_filtered.iloc[0]['nama_dosen']}"
                )

                st.success(
                    f"Rekomendasi terbaik (Jaccard): {jaccard_filtered.iloc[0]['nama_dosen']}"
                )

                # ================= EVALUASI =================
                st.subheader("📊 Evaluasi Sistem")

                from evaluasi import hitung_metrik
                import pandas as pd

                df_gt = pd.read_csv("Data Testing_fiks.csv", sep=";")
                df_gt.columns = df_gt.columns.str.lower().str.strip()
                df_gt["judul"] = df_gt["judul"].astype(str).str.lower().str.strip()

                judul_input = judul.lower().strip()
                row_match = df_gt[df_gt["judul"] == judul_input]

                if not row_match.empty:

                    row = row_match.iloc[0]

                    ground_truth = [
                        row["penguji 1"],
                        row["penguji 2"],
                        row["penguji 3"]
                    ]

                    ground_truth = [
                        str(d).lower().strip()
                        for d in ground_truth if pd.notna(d)
                    ]

                    # COSINE
                    p_c, r_c, n_c = hitung_metrik(
                        rekomendasi_cosine,
                        ground_truth,
                        k=10
                    )

                    # JACCARD
                    p_j, r_j, n_j = hitung_metrik(
                        rekomendasi_jaccard,
                        ground_truth,
                        k=10
                    )

                    st.markdown("### Cosine Similarity")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Precision@10", f"{p_c:.3f}")
                    col2.metric("Recall@10", f"{r_c:.3f}")
                    col3.metric("NDCG@10", f"{n_c:.3f}")

                    st.markdown("### Jaccard Similarity")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Precision@10", f"{p_j:.3f}")
                    col2.metric("Recall@10", f"{r_j:.3f}")
                    col3.metric("NDCG@10", f"{n_j:.3f}")

                    with st.expander("🔍 Detail Evaluasi"):
                        st.write("Ground Truth:", ground_truth)
                        st.write("Rekomendasi Cosine:", rekomendasi_cosine)
                        st.write("Rekomendasi Jaccard:", rekomendasi_jaccard)

                else:
                    st.warning("Data tidak ditemukan di ground truth.")





                # ================= EVALUASI TAMBAHAN =================
                st.subheader("📊 Evaluasi Tambahan (Bidang Keahlian)")

                from preprocess_bidang_evaluasi import preprocess_bidang, tambah_sinonim

                df_bidang = pd.read_csv("Ground Truth _ Bidang Keahlian Dosen.csv", sep=";")

                bidang_dict = {}

                for _, row in df_bidang.iterrows():
                    nama = row["nama_dosen"].lower().strip()
                    bidang = str(row["bidang_keahlian"])

                    bidang = preprocess_bidang(bidang)
                    bidang = tambah_sinonim(bidang)

                    bidang_dict[nama] = bidang

                # ==== query user ====
                query_text = topik + " " + judul + " " + abstrak
                query_text = preprocess_bidang(query_text)
                query_text = tambah_sinonim(query_text)

                def get_relevant_dosen(query, bidang_dict):
                    relevant = []

                    for dosen, bidang in bidang_dict.items():
                        for kata in query.split():
                            if kata in bidang:
                                relevant.append(dosen)
                                break

                    return relevant

                ground_truth_bidang = get_relevant_dosen(query_text, bidang_dict)

                # COSINE
                p_cb, r_cb, n_cb = hitung_metrik(
                    rekomendasi_cosine,
                    ground_truth_bidang,
                    k=10
                )

                # JACCARD
                p_jb, r_jb, n_jb = hitung_metrik(
                    rekomendasi_jaccard,
                    ground_truth_bidang,
                    k=10
                )

                st.markdown("### Cosine Similarity")
                col1, col2, col3 = st.columns(3)
                col1.metric("Precision@10 (Bidang)", f"{p_cb:.3f}")
                col2.metric("Recall@10 (Bidang)", f"{r_cb:.3f}")
                col3.metric("NDCG@10 (Bidang)", f"{n_cb:.3f}")

                st.markdown("### Jaccard Similarity")
                col1, col2, col3 = st.columns(3)
                col1.metric("Precision@10 (Bidang)", f"{p_jb:.3f}")
                col2.metric("Recall@10 (Bidang)", f"{r_jb:.3f}")
                col3.metric("NDCG@10 (Bidang)", f"{n_jb:.3f}")

                with st.expander("🔍 Detail Evaluasi Bidang"):
                    st.write("Ground Truth Bidang:", ground_truth_bidang)
                    st.write("Rekomendasi Cosine:", rekomendasi_cosine)
                    st.write("Rekomendasi Jaccard:", rekomendasi_jaccard)

            else:
                st.warning("Tidak ada dosen pada prodi yang dipilih.")






    elif menu == "Data Dosen":

        st.subheader("📊 Data Dosen")

        pilihan_prodi = st.selectbox(
            "Pilih Program Studi",
            ["Teknik Informatika", "Sistem Informasi"]
        )

        col1, col2 = st.columns([8,2])

        with col2:
            if st.button("➕ Tambah Data"):
                st.session_state.page = "tambah_dosen"
                st.rerun()

        conn = get_connection()

        query = """
        SELECT id_dosen, nama_dosen
        FROM dosen
        WHERE prodi = %s
        ORDER BY nama_dosen
        """

        df = pd.read_sql(query, conn, params=(pilihan_prodi,))
        conn.close()

        for i, row in df.iterrows():

            col1, col2, col3, col4, col5 = st.columns([1,5,2,2,3])

            col1.write(i+1)
            col2.write(row["nama_dosen"])

            if col3.button("✏️", key=f"edit{row['id_dosen']}"):
                st.session_state.edit_id = row["id_dosen"]
                st.session_state.page = "edit_dosen"
                st.rerun()

            if col4.button("🗑️", key=f"hapus{row['id_dosen']}"):
                st.session_state.hapus_id = row["id_dosen"]
                st.session_state.page = "hapus_dosen"
                st.rerun()

            if col5.button("📚 Penelitian", key=f"penelitian{row['id_dosen']}"):
                st.session_state.id_dosen_detail = row["id_dosen"]
                st.session_state.nama_dosen_detail = row["nama_dosen"]
                st.session_state.page = "detail_penelitian"
                st.rerun()


# ================= TAMBAH DOSEN =================
elif st.session_state.page == "tambah_dosen":

    st.title("Form Tambah Data Dosen")

    nama = st.text_input("Nama Dosen")

    prodi = st.selectbox(
        "Program Studi",
        ["Sistem Informasi", "Teknik Informatika"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Simpan"):

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO dosen (nama_dosen, prodi) VALUES (%s,%s)",
                (nama, prodi)
            )

            conn.commit()
            cur.close()
            conn.close()

            st.success("Data berhasil disimpan ✅")

            st.session_state.page = "dashboard_dosen"
            st.rerun()

    with col2:
        if st.button("⬅️ Kembali"):
            st.session_state.page = "dashboard_dosen"
            st.rerun()


# ================= EDIT DOSEN =================
elif st.session_state.page == "edit_dosen":

    id_edit = st.session_state.edit_id

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT nama_dosen, prodi FROM dosen WHERE id_dosen=%s",
        (id_edit,)
    )

    data = cur.fetchone()
    conn.close()

    nama = st.text_input("Nama Dosen", value=data[0])

    prodi = st.selectbox(
        "Program Studi",
        ["Sistem Informasi", "Teknik Informatika"],
        index=0 if data[1]=="Sistem Informasi" else 1
    )

    if st.button("Update"):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE dosen SET nama_dosen=%s, prodi=%s WHERE id_dosen=%s",
            (nama, prodi, id_edit)
        )

        conn.commit()
        conn.close()

        st.success("Data berhasil diupdate ✅")

        st.session_state.page = "dashboard_dosen"
        st.rerun()


# ================= HAPUS DOSEN =================
elif st.session_state.page == "hapus_dosen":

    st.warning("⚠️ Apakah anda yakin ingin menghapus data ini?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("YA HAPUS"):

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM penelitian_dosen WHERE id_dosen=%s",
                (st.session_state.hapus_id,)
            )

            cur.execute(
                "DELETE FROM dosen WHERE id_dosen=%s",
                (st.session_state.hapus_id,)
            )

            conn.commit()
            conn.close()

            st.success("Data berhasil dihapus")

            st.session_state.page = "dashboard_dosen"
            st.rerun()

    with col2:
        if st.button("BATAL"):
            st.session_state.page = "dashboard_dosen"
            st.rerun()


# ================= DAFTAR PENELITIAN =================
elif st.session_state.page == "detail_penelitian":

    id_dosen = st.session_state.id_dosen_detail
    nama = st.session_state.nama_dosen_detail

    st.title(f"Daftar Penelitian - {nama}")

    conn = get_connection()

    query = """
    SELECT id_penelitian, judul_penelitian
    FROM penelitian_dosen
    WHERE id_dosen = %s
    ORDER BY id_penelitian
    """

    df = pd.read_sql(query, conn, params=(id_dosen,))
    conn.close()

    for i, row in df.iterrows():

        col1, col2, col3, col4 = st.columns([1,8,2,2])

        col1.write(i+1)
        col2.write(row["judul_penelitian"])

        if col3.button("✏️", key=f"editp{row['id_penelitian']}"):
            st.session_state.edit_penelitian = row["id_penelitian"]
            st.session_state.page = "edit_penelitian"
            st.rerun()

        if col4.button("🗑️", key=f"hapusp{row['id_penelitian']}"):
            st.session_state.hapus_penelitian = row["id_penelitian"]
            st.session_state.page = "hapus_penelitian"
            st.rerun()

    st.divider()

    if st.button("➕ Tambah Penelitian"):
        st.session_state.page = "tambah_penelitian"
        st.rerun()

    if st.button("⬅️ Kembali ke Data Dosen"):
        st.session_state.page = "dashboard_dosen"
        st.rerun()


# ================= TAMBAH PENELITIAN =================
elif st.session_state.page == "tambah_penelitian":
    
    from backfill_judul_penelitian import translate_to_indonesia
    from backfill_judul_penelitian import preprocess_query

    st.title("Tambah Judul Penelitian")

    judul = st.text_area("Judul Penelitian")

    if st.button("Simpan"):

        if judul.strip() == "":
            st.warning("Judul tidak boleh kosong!")
        else:
            judul_translate = translate_to_indonesia(judul, "id")

            judul_preprocessed = preprocess_query(judul_translate)

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO penelitian_dosen 
                (id_dosen, judul_penelitian, judul_translate, judul_preprocessed) 
                VALUES (%s, %s, %s, %s)
                """,
                (
                    st.session_state.id_dosen_detail,
                    judul,
                    judul_translate,
                    judul_preprocessed
                )
            )

            conn.commit()
            conn.close()

            st.success("Berhasil tambah penelitian")

            st.session_state.page = "detail_penelitian"
            st.rerun()

# ================= EDIT PENELITIAN =================
elif st.session_state.page == "edit_penelitian":

    st.title("Edit Penelitian")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT judul_penelitian FROM penelitian_dosen WHERE id_penelitian=%s",
        (st.session_state.edit_penelitian,)
    )
    data = cur.fetchone()

    judul_baru = st.text_area("Judul Penelitian", value=data[0])

    if st.button("Update"):

        cur.execute(
            "UPDATE penelitian_dosen SET judul_penelitian=%s WHERE id_penelitian=%s",
            (judul_baru, st.session_state.edit_penelitian)
        )

        conn.commit()
        conn.close()

        st.success("Data berhasil diupdate")

        st.session_state.page = "detail_penelitian"
        st.rerun()

# ================= HAPUS PENELITIAN =================
elif st.session_state.page == "hapus_penelitian":

    st.warning("⚠️ Yakin ingin menghapus penelitian ini?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("YA HAPUS"):

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM penelitian_dosen WHERE id_penelitian=%s",
                (st.session_state.hapus_penelitian,)
            )

            conn.commit()
            conn.close()

            st.success("Data berhasil dihapus")

            st.session_state.page = "detail_penelitian"
            st.rerun()

    with col2:
        if st.button("BATAL"):
            st.session_state.page = "detail_penelitian"
            st.rerun()

            
# ================= DASHBOARD MAHASISWA =================
elif st.session_state.page == "dashboard_mhs":

        st.subheader("🔎 Cari Rekomendasi Penguji")

        topik = st.text_input("Topik Penelitian")
        judul = st.text_input("Judul Penelitian")
        abstrak = st.text_area("Abstrak")

        if st.button("Cari"):

            # VALIDASI
            if not (judul or abstrak or topik):
                st.warning("Input tidak boleh kosong!")
                st.stop()

            # ================= LOAD PICKLE =================
            import pickle
            from backfill_judul_penelitian import preprocess_query

            with open("model_rekomendasi.pkl", "rb") as f:
                model = pickle.load(f)

            tfidf_matrix = model["tfidf_matrix"]
            vocab = model["vocab"]
            idf = model["idf"]
            names = model["nama_dosen"]

            # ================= PREPROCESS QUERY =================
            query_text = topik + " " + judul + " " + abstrak
            query_tokens = preprocess_query(query_text)

            # ================= TF QUERY =================
            from collections import Counter

            def compute_tf(tokens):
                tf_dict = {}
                counter = Counter(tokens)
                max_freq = max(counter.values())

                for word, count in counter.items():
                    tf_dict[word] = count / max_freq

                return tf_dict

            tf_query = compute_tf(query_tokens)

            # ================= TF-IDF QUERY =================
            def compute_tfidf(tf, idf):
                tfidf = {}
                for word, val in tf.items():
                    if word in idf:
                        tfidf[word] = val * idf[word]
                return tfidf

            tfidf_query = compute_tfidf(tf_query, idf)

            # ================= VECTORIZE =================
            import numpy as np

            def vectorize(tfidf_dict, vocab):
                return np.array([tfidf_dict.get(word, 0) for word in vocab])

            query_vector = vectorize(tfidf_query, vocab)

            # ================= COSINE =================
            from numpy.linalg import norm

            def cosine_similarity(vec1, vec2):
                if norm(vec1) == 0 or norm(vec2) == 0:
                    return 0
                return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

            cosine_scores = [
                cosine_similarity(query_vector, doc)
                for doc in tfidf_matrix
            ]

            # ================= JACCARD =================
            def jaccard_similarity(vec1, vec2):
                vec1_bin = vec1 > 0
                vec2_bin = vec2 > 0

                intersection = np.logical_and(vec1_bin, vec2_bin).sum()
                union = np.logical_or(vec1_bin, vec2_bin).sum()

                if union == 0:
                    return 0
                return intersection / union

            jaccard_scores = [
                jaccard_similarity(query_vector, doc)
                for doc in tfidf_matrix
            ]

            # ================= AMBIL DATA DOSEN =================
            conn = get_connection()
            df_dosen = pd.read_sql(
                "SELECT nama_dosen, prodi FROM dosen",
                conn
            )
            conn.close()

            # ================= GABUNGKAN =================
            result = pd.DataFrame({
                "nama_dosen": names,
                "cosine": cosine_scores,
                "jaccard": jaccard_scores
            })

            df_dosen["nama_dosen"] = df_dosen["nama_dosen"].str.lower().str.strip()
            result["nama_dosen"] = result["nama_dosen"].str.lower().str.strip()

            result = result.merge(df_dosen, on="nama_dosen", how="left")

            # ================= SORTING =================
            # ranking cosine
            result_cosine = result.sort_values(by="cosine", ascending=False).copy()
            result_cosine["ranking"] = range(1, len(result_cosine)+1)

            # ranking jaccard
            result_jaccard = result.sort_values(by="jaccard", ascending=False).copy()
            result_jaccard["ranking"] = range(1, len(result_jaccard)+1)

            result_cosine = result_cosine[
                ["ranking", "nama_dosen", "prodi", "cosine", "jaccard"]
            ]

            result_jaccard = result_jaccard[
                ["ranking", "nama_dosen", "prodi", "cosine", "jaccard"]
            ]

            result_cosine["cosine"] = result_cosine["cosine"].round(4)
            result_cosine["jaccard"] = result_cosine["jaccard"].round(4)

            result_jaccard["cosine"] = result_jaccard["cosine"].round(4)
            result_jaccard["jaccard"] = result_jaccard["jaccard"].round(4)

            st.session_state["result_cosine"] = result_cosine
            st.session_state["result_jaccard"] = result_jaccard

        # ================= CEK HASIL =================

        if "result_cosine" in st.session_state:

            result_cosine = st.session_state["result_cosine"]
            result_jaccard = st.session_state["result_jaccard"]

            # ================= FILTER PRODI =================
            st.subheader("🎯 Filter Prodi")

            list_prodi = result_cosine["prodi"].dropna().unique().tolist()
            filter_options = ["Semua Prodi"] + sorted(list_prodi)

            selected_prodi = st.selectbox("Pilih Prodi:", filter_options)

            if selected_prodi == "Semua Prodi":
                st.info("Menampilkan semua prodi.")
                
                cosine_filtered = result_cosine.copy()
                jaccard_filtered = result_jaccard.copy()

            else:
                st.info(f"Menampilkan prodi: {selected_prodi}")
                
                cosine_filtered = result_cosine[
                    result_cosine["prodi"] == selected_prodi
                ].copy()

                jaccard_filtered = result_jaccard[
                    result_jaccard["prodi"] == selected_prodi
                ].copy()

            # reset ranking ulang
            cosine_filtered["ranking"] = range(1, len(cosine_filtered) + 1)
            jaccard_filtered["ranking"] = range(1, len(jaccard_filtered) + 1)

            # ================= TAMPILKAN =================
            st.subheader("📊 Top 10 Rekomendasi Dosen Penguji")

            st.markdown("### Cosine Similarity")
            st.dataframe(cosine_filtered.head(10), use_container_width=True)

            st.markdown("### Jaccard Similarity")
            st.dataframe(jaccard_filtered.head(10), use_container_width=True)

            if len(cosine_filtered) > 0 and len(jaccard_filtered) > 0:

                rekomendasi_cosine = cosine_filtered["nama_dosen"].head(10).tolist()
                rekomendasi_jaccard = jaccard_filtered["nama_dosen"].head(10).tolist()

                st.success(
                    f"Rekomendasi terbaik (Cosine): {cosine_filtered.iloc[0]['nama_dosen']}"
                )

                st.success(
                    f"Rekomendasi terbaik (Jaccard): {jaccard_filtered.iloc[0]['nama_dosen']}"
                )
            else:
                st.warning("Tidak ada rekomendasi ditemukan.")

        if st.button("Logout"):
            st.session_state.page = "login"
            st.session_state.pop("result_cosine", None)
            st.session_state.pop("result_jaccard", None)
            st.rerun()