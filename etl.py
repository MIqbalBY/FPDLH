# etl.py

import pdfplumber
import pandas as pd
import mysql.connector
import re
import os

def extract_and_transform(pdf_path):
    nrp = None
    nama = None
    tahun_masuk = None
    courses_data = []
    entry_year_from_nim_pattern = re.compile(r'^\d{4}(\d{2})')
    course_code_pattern = re.compile(r'^[A-Z]{2}\d{4,6}$')
    course_term_pattern = re.compile(r'(\d{4})/(Gs|Gn)')

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join(page.extract_text() or '' for page in pdf.pages)

            # Ekstrak NRP/NIM dan Nama sekali saja (hanya sampai akhir baris)
            nrp_nama_match = re.search(
                r'NRP\s*/\s*Nama\s*[:\s]*([0-9]{10})\s*/\s*([^\n]+)',
                full_text
            )
            if nrp_nama_match:
                nrp  = nrp_nama_match.group(1)
                nama = nrp_nama_match.group(2).strip()
                # buang sisa teks "SKS Tempuh" jika tertangkap
                nama = re.split(r'\bSKS Tempuh\b', nama)[0].strip()

            # Ekstrak tahun masuk dari NRP jika ditemukan
            if nrp:
                year_match = entry_year_from_nim_pattern.search(nrp)
                if year_match:
                    tahun_masuk = int(f"20{year_match.group(1)}")

            # Proses tabel untuk data mata kuliah
            for page in pdf.pages:
                for table in page.extract_tables():
                    for row in table:
                        cleaned = [str(c).replace('\n',' ').strip() if c else '' for c in row]
                        
                        # Pastikan baris adalah baris mata kuliah yang valid
                        if len(cleaned) >= 5 and course_code_pattern.match(cleaned[0]):
                            kode, nm, sks, historis, huruf = cleaned[:5]
                            
                            nama_semester = None
                            term_match = course_term_pattern.search(historis)
                            if term_match:
                                year, term_code = term_match.groups()
                                semester_name = "Gasal" if term_code == "Gs" else "Genap"
                                nama_semester = f"{semester_name} {year}/{int(year)+1}"

                            if sks.isdigit() and huruf.isalpha() and nama_semester:
                                courses_data.append({
                                    'id_mahasiswa': nrp,
                                    'nama_mahasiswa': nama,
                                    'tahun_masuk': tahun_masuk,
                                    'id_matakuliah': kode,
                                    'nama_matakuliah': nm,
                                    'jumlah_sks': int(sks),
                                    'nilai_huruf': huruf,
                                    'nama_semester': nama_semester # Semester untuk mata kuliah ini
                                })

    except Exception as e:
        print(f"  -> Gagal memproses file {os.path.basename(pdf_path)} karena error: {e}")
        return pd.DataFrame()
    
    if courses_data and nrp and nama and tahun_masuk:
        return pd.DataFrame(courses_data)
    return pd.DataFrame()


def load_data_to_db(df, db_params):
    """Memuat data ke dalam dimensi dan fact sesuai star schema baru."""
    if df.empty:
        return
    conn = mysql.connector.connect(**db_params)
    cur = conn.cursor()
    try:
        for _, row in df.iterrows():
            # upsert DimMahasiswa
            cur.execute(
                "INSERT INTO DimMahasiswa (id_mahasiswa, nama_mahasiswa, tahun_masuk) VALUES (%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE nama_mahasiswa=VALUES(nama_mahasiswa), tahun_masuk=VALUES(tahun_masuk)",
                (row['id_mahasiswa'], row['nama_mahasiswa'], row['tahun_masuk'])
            )
            # upsert DimMataKuliah
            cur.execute(
                "INSERT INTO DimMataKuliah (id_matakuliah, nama_matakuliah, jumlah_sks) VALUES (%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE nama_matakuliah=VALUES(nama_matakuliah), jumlah_sks=VALUES(jumlah_sks)",
                (row['id_matakuliah'], row['nama_matakuliah'], row['jumlah_sks'])
            )
            # upsert DimTerm
            sem_parts = row['nama_semester'].split()
            semester = sem_parts[0]
            tahun_akademik = int(sem_parts[1].split('/')[0])
            cur.execute(
                "INSERT INTO DimTerm (nama_semester, tahun_akademik, semester) VALUES (%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE tahun_akademik=VALUES(tahun_akademik)",
                (row['nama_semester'], tahun_akademik, semester)
            )
            # lookup surrogate keys
            cur.execute("SELECT mahasiswa_sk FROM DimMahasiswa WHERE id_mahasiswa=%s", (row['id_mahasiswa'],))
            res = cur.fetchone()
            lst = list(res) if res else []
            mahasiswa_sk = int(lst[0]) if lst else None  # type: ignore
            cur.execute("SELECT matakuliah_sk FROM DimMataKuliah WHERE id_matakuliah=%s", (row['id_matakuliah'],))
            res = cur.fetchone()
            lst = list(res) if res else []
            matakuliah_sk = int(lst[0]) if lst else None  # type: ignore
            cur.execute("SELECT term_sk FROM DimTerm WHERE nama_semester=%s", (row['nama_semester'],))
            res = cur.fetchone()
            lst = list(res) if res else []
            term_sk = int(lst[0]) if lst else None  # type: ignore
            cur.execute(
                "SELECT grade_sk, nilai_angka, keterangan_lulus FROM DimGrade WHERE nilai_huruf=%s", (row['nilai_huruf'],)
            )
            res = cur.fetchone()
            lst = list(res) if res else []
            grade_sk = int(lst[0]) if len(lst)>0 else None  # type: ignore
            nilai_angka = float(lst[1]) if len(lst)>1 else 0.0  # type: ignore
            ket_lulus = bool(lst[2]) if len(lst)>2 else False  # type: ignore
            sks_diperoleh = row['jumlah_sks'] if ket_lulus else 0
            bobot_nilai = nilai_angka * row['jumlah_sks']
            # prepare typed parameters
            js = int(row['jumlah_sks'])
            sksd = int(sks_diperoleh)
            bot = float(bobot_nilai)
            # insert FactEnrollment
            cur.execute(
                "INSERT INTO FactEnrollment (mahasiswa_sk, matakuliah_sk, term_sk, grade_sk, sks_diambil, sks_diperoleh, bobot_nilai) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE sks_diambil=VALUES(sks_diambil), sks_diperoleh=VALUES(sks_diperoleh), bobot_nilai=VALUES(bobot_nilai)",
                (mahasiswa_sk, matakuliah_sk, term_sk, grade_sk, js, sksd, bot)
            )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"  -> Gagal memuat data ke DB: {err}")
    finally:
        cur.close()
        conn.close()