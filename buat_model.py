"""ECOWATER SCHOOL - buat data SIMULASI lalu latih Decision Tree.
Jalankan:  python buat_model.py
Hasil: data_air_SIMULASI.csv dan model_air.pkl

PENTING: data ini dibuat dari aturan buatan kita sendiri, BUKAN data asli sekolah.
Akurasinya hanya menunjukkan model bisa menangkap aturan itu, bukan kemampuan di dunia nyata.
Kalau data asli sudah ada, ganti CSV-nya (kolom sama) dan jalankan ulang.
"""
import numpy as np
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

rng = np.random.default_rng(42)
N = 1500
AREA = ["L.RU", "Kelas 10", "Kelas 11", "Kelas 12"]

d = pd.DataFrame({
    "sesi": rng.choice(["pagi", "istirahat 1", "istirahat 2", "pulang"], N),
    "area": rng.choice(AREA, N),
    "jenis_titik": rng.choice(["tempat wudu", "wastafel", "toilet"], N),
    "kondisi_pdam": rng.choice(["hidup", "kecil", "mati"], N, p=[0.4, 0.35, 0.25]),
    "level_toren": rng.choice(["penuh", "setengah", "hampir habis"], N, p=[0.25, 0.4, 0.35]),
    "area_dialiri": rng.choice(AREA, N),
    "curah_hujan": rng.choice(["kering", "hujan"], N, p=[0.7, 0.3]),
})
d["sedang_dialiri"] = np.where(d["area"] == d["area_dialiri"], "ya", "tidak")

# Aturan simulasi: makin besar skor, makin rawan
skor = (
    d["kondisi_pdam"].map({"hidup": 0, "kecil": 1.2, "mati": 2.5})
    + d["level_toren"].map({"penuh": 0, "setengah": 1, "hampir habis": 2.5})
    + d["sesi"].map({"pagi": 0, "istirahat 1": 0.5, "istirahat 2": 1.2, "pulang": 0.2})
    + np.where(d["sedang_dialiri"] == "tidak", 1.5, 0)
    + np.where(d["area"] == "L.RU", 0.7, 0)
    + d["jenis_titik"].map({"tempat wudu": 0.5, "wastafel": 0.3, "toilet": 0})
    + np.where(d["curah_hujan"] == "kering", 0.5, 0)
    + rng.normal(0, 0.6, N)
)
d["kondisi_air"] = np.select([skor < 3, skor < 5.5], ["lancar", "kecil"], "habis")
d.drop(columns="sedang_dialiri").to_csv("data_air_SIMULASI.csv", index=False)

fitur = ["sesi", "area", "jenis_titik", "kondisi_pdam", "level_toren", "sedang_dialiri", "curah_hujan"]
X = pd.get_dummies(d[fitur])
y = d["kondisi_air"]
Xl, Xu, yl, yu = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = DecisionTreeClassifier(max_depth=5, random_state=42).fit(Xl, yl)

print("Sebaran kelas:\n", y.value_counts())
print("Akurasi data uji (data simulasi):", round(accuracy_score(yu, model.predict(Xu)) * 100, 1), "%")
print(export_text(model, feature_names=list(X.columns), max_depth=3))
joblib.dump({"model": model, "kolom": list(X.columns)}, "model_air.pkl")
print("Tersimpan: model_air.pkl")
