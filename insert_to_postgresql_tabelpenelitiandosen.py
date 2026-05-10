import pandas as pd
from koneksi import get_connection

df = pd.read_excel("data_clean.xlsx")

conn = get_connection()
cur = conn.cursor()

df.columns = df.columns.str.strip().str.lower()

for index, row in df.iterrows():
    id_dosen = int(row["id_dosen"])
    judul = str(row["judul_penelitian"]).strip()

    if judul == "" or judul.lower() == "nan":
        continue

    cur.execute(
        """
        SELECT 1 FROM penelitian_dosen
        WHERE id_dosen=%s AND judul_penelitian=%s
        """,
        (id_dosen, judul)
    )

    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO penelitian_dosen (id_dosen, judul_penelitian)
            VALUES (%s,%s)
            """,
            (id_dosen, judul)
        )

conn.commit()
cur.close()
conn.close()

print("IMPORT SELESAI")