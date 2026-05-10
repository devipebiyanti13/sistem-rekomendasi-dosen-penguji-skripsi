# import pandas as pd
# import os

# # lokasi folder berisi file dosen
# folder_path = "SISTEM INFORMASI"

# data_semua = []

# for file in os.listdir(folder_path):
#     if file.endswith(".csv") or file.endswith(".xlsx"):
        
#         nama_dosen = os.path.splitext(file)[0]   # ambil nama file tanpa ekstensi
        
#         file_path = os.path.join(folder_path, file)

#         # baca file
#         if file.endswith(".csv"):
#             df = pd.read_csv(file_path)
#         else:
#             df = pd.read_excel(file_path)

#         # ambil kolom Title saja
#         for judul in df["Title"].dropna():
#             data_semua.append({
#                 "nama_dosen": nama_dosen,
#                 "prodi": "Sistem Informasi",
#                 "judul_penelitian": judul
#             })

# # jadikan dataframe
# hasil = pd.DataFrame(data_semua)

# # simpan ke csv gabungan
# hasil.to_csv("Data Clean1.csv", index=False)

# print("✅ File CSV berhasil dibuat!")



# import pandas as pd

# df = pd.read_csv("Data Clean.csv", sep=";")
# df.to_excel("data_clean.xlsx", index=False)

# print("✅ Berhasil diubah ke XLSX")

