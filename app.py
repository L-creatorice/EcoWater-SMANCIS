import base64
import io
import json
import os
from datetime import datetime

import joblib
import pandas as pd
import streamlit as st
from PIL import Image

st.set_page_config(page_title="ECOWATER SCHOOL", page_icon="💧", layout="wide")

PIN_SARPRAS = "sarpras123"  # GANTI sebelum dipakai
AREA = ["L.RU", "Kelas 10", "Kelas 11", "Kelas 12"]
TITIK = ["tempat wudu", "wastafel", "toilet"]
SESI = ["pagi", "istirahat 1", "istirahat 2", "pulang"]
STATUS = {"lancar": ("AMAN", "🟢"), "kecil": ("WASPADA", "🟡"), "habis": ("RAWAN", "🔴")}
TOREN_PERSEN = {"penuh": 92, "setengah": 50, "hampir habis": 14}

# Posisi tengah tiap area di gambar denah (piksel gambar asli). EDIT kalau kurang pas.
POSISI = {"L.RU": (950, 545), "Kelas 10": (1150, 690), "Kelas 11": (600, 520), "Kelas 12": (1170, 440)}
GESER = {"tempat wudu": (-48, 0), "wastafel": (0, 0), "toilet": (48, 0)}
HURUF = {"tempat wudu": "W", "wastafel": "S", "toilet": "T"}

BASE = os.path.dirname(os.path.abspath(__file__))
F_STATUS = os.path.join(BASE, "status_terakhir.json")
F_LOG = os.path.join(BASE, "data_sarpras_log.csv")
F_LAPOR = os.path.join(BASE, "laporan_siswa.csv")
F_DENAH = os.path.join(BASE, "denah.jpeg")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Poppins:wght@400;500;600&display=swap');
html, body, .stApp, p, label, span, div { font-family: 'Poppins', sans-serif; }
h1, h2, h3, .judul { font-family: 'Fredoka', sans-serif !important; color: #0b4f6c; }
.stApp { background: linear-gradient(180deg, #d4f1ff 0%, #eaf9ff 45%, #ffffff 100%); }
header[data-testid="stHeader"] { background: transparent; }
.bubble { position: fixed; bottom: -80px; border-radius: 50%; background: rgba(56,189,248,.16);
  border: 1px solid rgba(56,189,248,.35); animation: rise linear infinite; z-index: 0; pointer-events: none; }
@keyframes rise { to { transform: translateY(-125vh); } }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-18px); } }
@keyframes fadeup { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: none; } }
@keyframes slide { to { -webkit-mask-position: 60px 0; mask-position: 60px 0; } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(215,55,55,.75); } 100% { box-shadow: 0 0 0 20px rgba(215,55,55,0); } }
.welcome { text-align: center; padding: 6vh 0 2vh; animation: fadeup .9s ease both; }
.welcome .tetes { font-size: 84px; display: inline-block; animation: bounce 2s ease-in-out infinite; }
.welcome .kecil { font-size: 1.15rem; color: #2b7a99; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px; }
.welcome .besar { font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: clamp(2.6rem, 8vw, 5rem); line-height: 1.05;
  background: linear-gradient(90deg, #0284c7, #06b6d4, #2563eb); -webkit-background-clip: text; background-clip: text; color: transparent; }
.welcome .tagline { max-width: 560px; margin: 14px auto 0; color: #35657a; font-size: 1.1rem; animation: fadeup 1.2s .3s ease both; }
.chips { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin: 22px 0 6px; }
.chip { background: #fff; border-radius: 999px; padding: 8px 18px; box-shadow: 0 4px 14px rgba(3,105,161,.15);
  font-weight: 500; color: #0b4f6c; animation: fadeup 1s ease both; }
.chip:nth-child(1) { animation-delay: .5s; } .chip:nth-child(2) { animation-delay: .7s; } .chip:nth-child(3) { animation-delay: .9s; }
.hero { background: linear-gradient(110deg, #0369a1, #0ea5e9 60%, #22d3ee); color: #fff; border-radius: 22px; padding: 22px 28px;
  box-shadow: 0 10px 30px rgba(3,105,161,.3); margin-bottom: 14px; animation: fadeup .6s ease both; }
.hero .t { font-family: 'Fredoka', sans-serif; font-size: 2rem; font-weight: 700; }
.hero .s { opacity: .92; }
.badge { display: inline-block; background: rgba(255,255,255,.22); border-radius: 999px; padding: 2px 12px; font-size: .8rem; margin-top: 8px; }
.stTabs [data-baseweb="tab"] { font-family: 'Fredoka', sans-serif; font-size: 1.1rem; }
.stButton > button { border-radius: 999px; background: linear-gradient(90deg, #0ea5e9, #2563eb); color: #fff; border: 0;
  padding: .55rem 1.8rem; font-weight: 600; transition: transform .15s, box-shadow .15s; box-shadow: 0 6px 16px rgba(37,99,235,.3); }
.stButton > button:hover { transform: scale(1.06); color: #fff; box-shadow: 0 10px 22px rgba(37,99,235,.4); }
.peta { position: relative; border-radius: 18px; overflow: hidden; box-shadow: 0 10px 34px rgba(3,105,161,.28); background: #fff; }
.peta img { width: 100%; display: block; }
.lab { position: absolute; transform: translate(-50%,-50%); background: rgba(255,255,255,.92); padding: 1px 9px; border-radius: 999px;
  font: 600 12px 'Poppins', sans-serif; color: #0b4f6c; box-shadow: 0 2px 6px rgba(0,0,0,.2); }
.dot { position: absolute; width: 2.6%; min-width: 20px; aspect-ratio: 1; transform: translate(-50%,-50%); border-radius: 50%;
  border: 3px solid #fff; color: #fff; font: 700 12px 'Poppins', sans-serif; display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: transform .2s; box-shadow: 0 2px 8px rgba(0,0,0,.35); }
.dot:hover { transform: translate(-50%,-50%) scale(1.4); z-index: 5; }
.dot.lancar { background: #2ea043; } .dot.kecil { background: #f0b400; }
.dot.habis { background: #d73737; animation: pulse 1.4s infinite; }
.tankwrap { text-align: center; }
.tank { position: relative; width: 120px; height: 200px; margin: 0 auto; border: 5px solid #0b4f6c; border-radius: 16px 16px 26px 26px;
  background: #f0faff; overflow: hidden; box-shadow: inset 0 0 14px rgba(11,79,108,.2), 0 8px 18px rgba(3,105,161,.2); }
.water { position: absolute; bottom: 0; left: 0; width: 100%; background: var(--c); transition: height 1.2s ease; }
.water::before { content: ""; position: absolute; top: -13px; left: 0; width: 100%; height: 14px; background: var(--c);
  -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 14'><path d='M0 7Q15 0 30 7T60 7V14H0Z'/></svg>") repeat-x;
  mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 14'><path d='M0 7Q15 0 30 7T60 7V14H0Z'/></svg>") repeat-x;
  -webkit-mask-size: 60px 14px; mask-size: 60px 14px; animation: slide 2.2s linear infinite; }
.pct { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font: 700 1.6rem 'Fredoka', sans-serif;
  color: #0b4f6c; text-shadow: 0 0 6px #fff; }
.tlabel { margin-top: 8px; font-weight: 600; color: #0b4f6c; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
st.markdown("".join(
    f"<span class='bubble' style='left:{l}%;width:{w}px;height:{w}px;animation-duration:{d}s;animation-delay:{dl}s'></span>"
    for l, w, d, dl in [(5, 30, 16, 0), (18, 18, 12, 3), (32, 44, 20, 6), (47, 22, 14, 1), (61, 36, 18, 8),
                        (74, 16, 11, 4), (86, 40, 22, 2), (94, 24, 15, 7)]), unsafe_allow_html=True)


@st.cache_resource
def muat_model():
    paket = joblib.load(os.path.join(BASE, "model_air.pkl"))
    return paket["model"], paket["kolom"]


@st.cache_data
def data_denah():
    if not os.path.exists(F_DENAH):
        return None, (1600, 1130)
    img = Image.open(F_DENAH).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode(), img.size


model, kolom = muat_model()


def prediksi(sesi, area, titik, pdam, toren, dialiri, hujan):
    baris = pd.DataFrame([{
        "sesi": sesi, "area": area, "jenis_titik": titik, "kondisi_pdam": pdam,
        "level_toren": toren, "sedang_dialiri": "ya" if area == dialiri else "tidak",
        "curah_hujan": hujan,
    }])
    baris = pd.get_dummies(baris).reindex(columns=kolom, fill_value=0)
    return model.predict(baris)[0]


def tabel_tiap_titik(sesi, s):
    return {(a, t): prediksi(sesi, a, t, s["pdam"], s["toren"], s["dialiri"], s["hujan"]) for a in AREA for t in TITIK}


def simpan_csv(path, baris):
    pd.DataFrame([baris]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def html_denah(hasil):
    b64, (w, h) = data_denah()
    isi = f"<img src='data:image/jpeg;base64,{b64}'>" if b64 else f"<div style='aspect-ratio:{w}/{h}'></div>"
    for area, (cx, cy) in POSISI.items():
        isi += f"<div class='lab' style='left:{cx / w * 100:.2f}%;top:{(cy - 42) / h * 100:.2f}%'>{area}</div>"
        for titik, (dx, dy) in GESER.items():
            st_ = hasil[(area, titik)]
            isi += (f"<div class='dot {st_}' title='{area} - {titik}: {STATUS[st_][0]}' "
                    f"style='left:{(cx + dx) / w * 100:.2f}%;top:{(cy + dy) / h * 100:.2f}%'>{HURUF[titik]}</div>")
    return f"<div class='peta'>{isi}</div>"


def html_toren(level):
    p = TOREN_PERSEN[level]
    warna = "#ef4444" if p < 30 else "#0ea5e9"
    return (f"<div class='tankwrap'><div class='tank'><div class='water' style='height:{p}%;--c:{warna}'></div>"
            f"<div class='pct'>{p}%</div></div><div class='tlabel'>Toren: {level}</div></div>")


# ---------------- LAYAR SELAMAT DATANG ----------------
if not st.session_state.get("masuk"):
    st.markdown("""<div class='welcome'><div class='tetes'>💧</div>
<div class='kecil'>Selamat datang di</div>
<div class='besar'>ECOWATER SCHOOL</div>
<div class='tagline'>Cek dulu sebelum wudu. Tidak perlu lagi keliling mencari keran yang masih mengalir di SMAN 1 Cisarua.</div>
<div class='chips'><span class='chip'>🗺️ Denah air real-time</span><span class='chip'>🤖 Prediksi machine learning</span><span class='chip'>🌱 Hemat air sekolah</span></div></div>""",
                unsafe_allow_html=True)
    _, tengah, _ = st.columns([1, 1, 1])
    with tengah:
        if st.button("Mulai 💧", use_container_width=True):
            st.session_state["masuk"] = True
            st.rerun()
    st.stop()

# ---------------- HALAMAN UTAMA ----------------
st.markdown("""<div class='hero'><div class='t'>💧 ECOWATER SCHOOL</div>
<div class='s'>Sistem Prediksi Kerentanan Air Bersih - SMAN 1 Cisarua</div>
<span class='badge'>Prototipe - model dilatih dengan data simulasi</span></div>""", unsafe_allow_html=True)

tab_siswa, tab_sarpras, tab_tentang = st.tabs(["🧑‍🎓 Siswa", "🛠️ Sarpras", "ℹ️ Tentang Sistem"])

with tab_siswa:
    if not os.path.exists(F_STATUS):
        st.info("Petugas sarpras belum mengisi kondisi hari ini. Denah akan muncul setelah data diisi.")
    else:
        s = json.load(open(F_STATUS))
        st.caption(f"Terakhir diperbarui petugas: **{s['waktu']}**")
        sesi = st.radio("Sesi", SESI, index=SESI.index(s["sesi"]), horizontal=True)
        hasil = tabel_tiap_titik(sesi, s)
        kiri, kanan = st.columns([3, 1])
        with kiri:
            st.markdown(html_denah(hasil), unsafe_allow_html=True)
            st.caption("W = tempat wudu, S = wastafel, T = toilet  |  🟢 aman  🟡 waspada  🔴 rawan (berdenyut). Arahkan kursor ke titik untuk detail.")
        with kanan:
            st.markdown(html_toren(s["toren"]), unsafe_allow_html=True)
            st.caption(f"PDAM: **{s['pdam']}**")
            st.subheader("Mau wudu?")
            baik = [a for a in AREA if hasil[(a, "tempat wudu")] == "lancar"]
            sedang = [a for a in AREA if hasil[(a, "tempat wudu")] == "kecil"]
            if baik:
                st.success("Tempat wudu aman: " + ", ".join(baik))
            elif sedang:
                st.warning("Tidak ada yang aman. Masih kecil di: " + ", ".join(sedang))
            else:
                st.error("Semua tempat wudu diperkirakan rawan habis.")
        with st.expander("📣 Lapor kondisi air sekarang"):
            la = st.selectbox("Area", AREA, key="la")
            lt = st.selectbox("Titik", TITIK, key="lt")
            lk = st.radio("Kondisi", ["lancar", "kecil", "habis"], horizontal=True, key="lk")
            if st.button("Kirim laporan"):
                simpan_csv(F_LAPOR, {"waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "sesi": sesi,
                                     "area": la, "jenis_titik": lt, "kondisi_air": lk})
                st.success("Terima kasih, laporanmu tersimpan. 💙")
                st.balloons()

with tab_sarpras:
    if not st.session_state.get("sarpras_ok"):
        pin = st.text_input("PIN petugas", type="password")
        if st.button("Masuk"):
            if pin.strip() == PIN_SARPRAS:
                st.session_state["sarpras_ok"] = True
                st.rerun()
            else:
                st.error("PIN salah.")
        else:
            st.info("Masukkan PIN lalu klik tombol Masuk.")
    else:
        st.subheader("Isi kondisi saat ini")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            sesi_s = st.selectbox("Sesi", SESI, key="ss")
            pdam = st.selectbox("Kondisi PDAM", ["hidup", "kecil", "mati"])
        with c2:
            toren = st.selectbox("Level toren", ["penuh", "setengah", "hampir habis"])
            dialiri = st.selectbox("Area yang sedang dialiri", AREA)
            hujan = st.selectbox("Cuaca hari ini", ["kering", "hujan"])
        with c3:
            st.markdown(html_toren(toren), unsafe_allow_html=True)
        if st.button("Simpan dan prediksi"):
            s = {"waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "sesi": sesi_s,
                 "pdam": pdam, "toren": toren, "dialiri": dialiri, "hujan": hujan}
            json.dump(s, open(F_STATUS, "w"))
            simpan_csv(F_LOG, {"waktu": s["waktu"], "sesi": sesi_s, "kondisi_pdam": pdam,
                               "level_toren": toren, "area_dialiri": dialiri, "curah_hujan": hujan})
            st.success("Tersimpan. Denah di tab Siswa sudah diperbarui.")
            h = tabel_tiap_titik(sesi_s, s)
            st.dataframe(pd.DataFrame([{"Area": a, "Titik": t, "Status": STATUS[h[(a, t)]][0]} for a in AREA for t in TITIK]),
                         hide_index=True, use_container_width=True)

with tab_tentang:
    st.markdown("""
**Alur sistem:** Input (petugas isi PDAM, toren, area dialiri, cuaca) → Proses (Decision Tree menebak) → Output (denah berwarna untuk siswa).

**Cara baca:** 🟢 aman = air diperkirakan lancar, 🟡 waspada = kecil, 🔴 rawan = habis.

**Keterbatasan:** model masih dilatih dari data simulasi. Setiap isian petugas dan laporan siswa tersimpan di file CSV
(`data_sarpras_log.csv`, `laporan_siswa.csv`) sebagai bahan data asli untuk melatih ulang model.
""")
