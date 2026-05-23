import os
import sqlite3
import streamlit as st

# === MENGUNCI LOKASI FOLDER DATABASE ===
FOLDER_SCRIPT = os.path.dirname(os.path.abspath(__file__)) if __file__ else "."
PATH_DATABASE = os.path.join(FOLDER_SCRIPT, "FOOD_MONITOR.db")


# ==========================================
# 1. FUNGSI DATABASE (SQLite)
# ==========================================
def inisialisasi_database():
    """Membuat file database dan tabel log jika belum ada."""
    conn = sqlite3.connect(PATH_DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS log_kesegaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            komoditas TEXT NOT NULL,
            suhu REAL NOT NULL,
            durasi_hari REAL NOT NULL,
            skor_kesegaran REAL NOT NULL,
            status TEXT NOT NULL,
            waktu_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def simpan_ke_sqlite(jenis, suhu, hari, skor, status):
    """Menyimpan hasil analisis ke dalam database lokal."""
    conn = sqlite3.connect(PATH_DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO log_kesegaran (komoditas, suhu, durasi_hari, skor_kesegaran, status)
        VALUES (?, ?, ?, ?, ?)
    """,
        (jenis, suhu, hari, skor, status),
    )
    conn.commit()
    conn.close()


# ==========================================
# 2. LOGIKA BIOPROSES BERDASARKAN LITERATUR JURNAL
# ==========================================
def hitung_kesegaran(suhu, hari, jenis_pangan):
    jenis_lower = jenis_pangan.lower()
    max_hari = 1.0
    penjelasan = ""

    # --- KATEGORI 1: DAGING AYAM ---
    if "ayam" in jenis_lower:
        if suhu <= -10:
            max_hari = 300
            if suhu > -18:
                max_hari = 45
                penjelasan = "Analisis Jurnal Mikrobiologi: Suhu freezer tidak stabil (> -10°C) memicu pertumbuhan kristal es besar yang merusak dinding sel. Bakteri Salmonella Enteritidis memang dorman, tetapi degradasi kualitas sensorik berjalan 5x lebih cepat."
            else:
                penjelasan = f"Analisis Jurnal (Food Control): Pada suhu ideal {suhu}°C, bakteri patogen seperti Campylobacter jejuni terhenti total. Penyimpanan {hari} hari aman secara mikrobiologis, namun oksidasi asam lemak tak jenuh tinggi pada unggas mulai berjalan lambat."
        elif suhu <= 4:
            max_hari = 2.0
            penjelasan = "Analisis Jurnal: Di bawah suhu 4°C (kulkas), bakteri psikrotrofik (Pseudomonas spp.) mengontrol ekosistem daging. Memasuki batas waktu simpan, metabolisme bakteri mulai memproduksi lendir dan bau amonia."
        else:
            max_hari = 0.16
            penjelasan = "⚠️ PERINGATAN BAHAYA (Standar CDC): Suhu lingkungan > 5°C memicu fase log (pembelahan eksponensial) Salmonella dan Campylobacter. Bakteri berkembang biak setiap 20 menit, membuat daging sangat berisiko memicu Salmonellosis."

    # --- KATEGORI 2: DAGING SAPI ---
    elif "sapi" in jenis_lower:
        if suhu <= -10:
            max_hari = 270
            if suhu > -18:
                max_hari = 60
                penjelasan = "Analisis Jurnal (Meat Science): Fluktuasi suhu freezer menyebabkan dehidrasi permukaan daging. Es menyublim langsung ke udara, mempercepat kerusakan struktural protein dan perubahan warna mioglobin."
            else:
                penjelasan = (
                    f"Analisis Jurnal (Food Chemistry):\nPada kondisi {suhu}°C selama {hari} hari, aktivitas bakteri patogen (E. coli O157:H7 dan Salmonella spp.) lumpuh total. "
                    f"Namun, penyimpanan jangka panjang (> 60 hari) memicu denaturasi protein protein struktural dan oksidasi lipid (lemak). "
                    f"Ini menyebabkan hilangnya kemampuan mengikat air (water-holding capacity), memicu timbulnya 'freezer burn' yang membuat tekstur daging menjadi kering dan kehilangan juiciness saat diolah."
                )
        elif suhu <= 4:
            max_hari = 4.0
            penjelasan = "Analisis Standar FDA: Suhu chiller (0–4°C) menahan laju bakteri mesofilik. Namun, kolonisasi bakteri pembusuk (Brochothrix thermosphacta) tetap berjalan secara konstan dan memicu degradasi warna merah daging setelah hari ke-4."
        else:
            max_hari = 0.08
            penjelasan = "⚠️ PERINGATAN KRITIS: Pada suhu ruang, daging sapi melepaskan drip loss (darah/cairan seluler) yang kaya akan asam amino. Bakteri Eschericia coli berkembang sangat agresif, memproduksi toksin berbahaya dalam waktu singkat."

    # --- KATEGORI 3: DAGING IKAN ---
    elif "ikan" in jenis_lower:
        if suhu <= -10:
            max_hari = 120
            penjelasan = f"Analisis Jurnal (FAO Statistics): Jaringan ikat ikan sangat longgar. Pada suhu {suhu}°C mikroba mati, namun proses degradasi kimia enzimatis tetap berjalan, mengubah senyawa Trimethylamine Oxide (TMAO) menjadi TMA penyebab bau amis pekat."
        elif suhu <= 2:
            max_hari = 2.0
            penjelasan = "Analisis Literatur: Ikan dihuni oleh bakteri psikrofilik alami dari laut (Shewanella putrefaciens). Rentang suhu 0–2°C adalah pertahanan maksimal sebelum enzim autolitik merombak protein tekstur menjadi lembek."
        elif suhu <= 4:
            max_hari = 1.0
            penjelasan = "Analisis Jurnal: Suhu kulkas biasa (4°C) kurang dingin untuk komoditas laut. Bakteri pembusuk aktif 2x lipat lebih cepat dibanding suhu 0°C, memicu penurunan kesegaran insang dan mata ikan secara drastis."
        else:
            max_hari = 0.06
            penjelasan = "⚠️ BAHAYA TOKSIN: Komoditas scombroid (seperti tongkol/tuna) di suhu ruang mengalami dekarboksilasi histidin menjadi histamin oleh bakteri. Ini memicu keracunan Scombroid Poisoning (alergi akut mendadak)."

    # --- KATEGORI 4: DAGING KAMBING ---
    elif "kambing" in jenis_lower:
        if suhu <= -10:
            max_hari = 225
            penjelasan = f"Analisis Jurnal: Pembekuan menjaga keutuhan struktur miosin daging kambing. Pada hari ke-{hari}, kristalisasi mengunci mikroba patogen seperti Clostridium perfringens agar tidak memproduksi toksin beracun."
        elif suhu <= 4:
            max_hari = 4.0
            penjelasan = "Analisis Literatur: Suhu kulkas meredam mikroba pembusuk. Namun lambat laun, asam lemak rantai cabang khas kambing (branched-chain fatty acids) mengalami kontak udara, memicu peningkatan bau prengus yang tajam."
        else:
            max_hari = 0.16
            penjelasan = "⚠️ PERINGATAN: Pembusukan berjalan aerobik. Bakteri Pseudomonas mempercepat degradasi protein daging kambing menjadi senyawa sulfur volatil, merusak total aroma dan mengundang lalat pembawa kontaminan."

    # --- KATEGORI 5: FROZEN FOOD ---
    elif "beku" in jenis_lower or "frozen" in jenis_lower:
        if suhu <= -18:
            max_hari = 270
            penjelasan = f"Analisis Cold Chain System: Regulasi rantai dingin global mewajibkan suhu tetap di bawah -18°C. Selama kestabilan ini terjaga, emulsi dan formulasi bahan baku pangan beku terlindungi dari kontaminasi eksternal."
        elif suhu <= 4:
            max_hari = 2.0
            penjelasan = "Analisis Pasca-Thawing: Setelah dicairkan di chiller, produk hanya bertahan 48 jam. Bakteri psikrotrofik tahan dingin seperti Listeria monocytogenes dapat mulai terbangun dan bereplikasi secara perlahan."
        else:
            max_hari = 0.16
            penjelasan = "⚠️ DILARANG MEMBEKUKAN ULANG (Refreezing): Jika mencair di atas suhu ruang, spora bakteri aktif kembali. Membekukannya lagi hanya akan mengunci jutaan bakteri yang siap memicu pembusukan instan saat dicairkan nanti."

    # --- KALKULASI AKHIR ---
    persentase_rusak = (hari / max_hari) * 100
    sisa_kesegaran = max(0.0, 100.0 - persentase_rusak)

    if sisa_kesegaran >= 80:
        return (
            round(sisa_kesegaran, 2),
            "Sangat Segar (Aman Dikonsumsi)",
            "green",
            penjelasan,
        )
    elif 30 < sisa_kesegaran < 80:
        return (
            round(sisa_kesegaran, 2),
            "Layak (Segera Olah / Masak!)",
            "orange",
            penjelasan,
        )
    else:
        return (0.0, "Busuk/Bahaya Mikroba Akut!", "red", penjelasan)


# ==========================================
# 3. INTERFACE WEB (STREAMLIT)
# ==========================================
# Set halaman web agar menggunakan tema gelap bawaan yang modern
st.set_page_config(page_title="Smart Meat Monitor v4.0", page_icon="🥩", layout="centered")

inisialisasi_database()

st.title("🥩 SMART MEAT MONITOR")
st.caption("Sistem analisis kelayakan dan bioproses daging berbasis literatur mikrobiologi")
st.divider()

# Buat form input data
with st.form("input_form"):
    st.subheader("Data Komoditas")

    jenis_pangan = st.selectbox(
        "Pilih Kategori Daging:",
        [
            "Daging ayam 🍗",
            "Daging sapi 🥩",
            "Daging ikan 🐟",
            "Daging kambing 🐐",
            "Daging beku/frozen food 🧊",
        ],
    )

    suhu = st.number_input("Suhu Penyimpanan (°C):", value=-18.0, step=1.0)
    hari = st.number_input("Durasi Penyimpanan (Hari):", value=70.0, min_value=0.0, step=1.0)

    # Tombol submit form
    submit_button = st.form_submit_button(label="MULAI ANALISIS SISTEM")

# Logika setelah tombol analisis ditekan
if submit_button:
    skor, status, warna, penjelasan = hitung_kesegaran(suhu, hari, jenis_pangan)

    # Tampilkan skor menggunakan komponen visual besar (Metric)
    st.markdown("### Hasil Analisis:")

    if warna == "green":
        st.success(f"Status: {status} | Skor Kesegaran: {skor}%")
    elif warna == "orange":
        st.warning(f"Status: {status} | Skor Kesegaran: {skor}%")
    else:
        st.error(f"Status: {status} | Skor Kesegaran: {skor}%")

    # Panel Informasi Jurnal
    st.info(f"**DEKLARASI ILMIAH & LITERATUR MIKROBIOLOGI**\n\n{penjelasan}")

    # Simpan data otomatis/langsung ketika sukses analisis (atau lewat tombol jika diperlukan)
    # Di web, kita bisa langsung simpan demi kemudahan user experience
    try:
        simpan_ke_sqlite(jenis_pangan, suhu, hari, skor, status)
        st.toast("Data berhasil disimpan ke database lokal!", icon="🗄️")
    except Exception as e:
        st.error(f"Gagal menyimpan ke database: {str(e)}")