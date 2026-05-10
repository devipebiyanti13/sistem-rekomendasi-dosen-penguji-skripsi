import pandas as pd
from koneksi import get_connection

df = pd.read_csv("data_dosen_si_infor.csv", delimiter=';')

conn = get_connection()
cur = conn.cursor()

print(df.columns.tolist())

for index, row in df.iterrows():
    nama = row["nama_dosen"]
    prodi = row["prodi"]
    bidang = row["bidang_minat"]

    cur.execute(
        "INSERT INTO dosen (nama_dosen, prodi, bidang_minat) VALUES (%s,%s,%s)",
        (nama, prodi, bidang)
    )

conn.commit()
cur.close()
conn.close()

print("IMPORT DOSEN SELESAI")