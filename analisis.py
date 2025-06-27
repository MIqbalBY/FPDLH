import mysql.connector
import pandas as pd

def calculate_gpa(db_params):
    """Menghitung IPK untuk setiap mahasiswa berdasarkan FactEnrollment."""
    conn = mysql.connector.connect(**db_params)
    query = """
        SELECT
            m.id_mahasiswa,
            m.nama_mahasiswa,
            SUM(f.bobot_nilai) / SUM(f.sks_diambil) AS ipk
        FROM FactEnrollment f
        JOIN DimMahasiswa m ON f.mahasiswa_sk = m.mahasiswa_sk
        JOIN DimGrade g ON f.grade_sk = g.grade_sk
        WHERE g.keterangan_lulus = 1
        GROUP BY m.id_mahasiswa, m.nama_mahasiswa
        ORDER BY ipk DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def print_gpa_rankings(df):
    """Mencetak peringkat IPK."""
    print("Peringkat IPK Mahasiswa")
    print("------------------------")
    for index, row in df.iterrows():
        print(f"{index + 1}. {row['nama_mahasiswa']}: {row['ipk']:.2f}")

def get_course_failure_rate(db_params):
    """Menghitung tingkat kegagalan (nilai E) per mata kuliah."""
    conn = mysql.connector.connect(**db_params)
    query = """
        SELECT
            d.nama_matakuliah,
            SUM(CASE WHEN g.nilai_huruf = 'E' THEN 1 ELSE 0 END) / COUNT(*) AS failure_rate
        FROM FactEnrollment f
        JOIN DimMataKuliah d ON f.matakuliah_sk = d.matakuliah_sk
        JOIN DimGrade g ON f.grade_sk = g.grade_sk
        GROUP BY d.nama_matakuliah
        ORDER BY failure_rate DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    print("\nTingkat Kegagalan Mata Kuliah (% nilai E):")
    print(df.to_string(index=False, formatters={'failure_rate': '{:.2%}'.format}))
    return df

def get_student_transcript(db_params, student_id):
    """Menampilkan riwayat transkrip mahasiswa berdasarkan id_mahasiswa (natural key)."""
    conn = mysql.connector.connect(**db_params)
    query = """
        SELECT
            m.id_mahasiswa,
            m.nama_mahasiswa,
            t.nama_semester,
            d.nama_matakuliah,
            d.jumlah_sks,
            g.nilai_huruf,
            f.bobot_nilai
        FROM FactEnrollment f
        JOIN DimMahasiswa m ON f.mahasiswa_sk = m.mahasiswa_sk
        JOIN DimTerm t ON f.term_sk = t.term_sk
        JOIN DimMataKuliah d ON f.matakuliah_sk = d.matakuliah_sk
        JOIN DimGrade g ON f.grade_sk = g.grade_sk
        WHERE m.id_mahasiswa = %s
        ORDER BY t.tahun_akademik, t.semester;
    """
    df = pd.read_sql_query(query, conn, params=(student_id,))
    conn.close()
    if df.empty:
        print(f"Tidak ditemukan data transkrip untuk mahasiswa: {student_id}")
    else:
        print(f"\nTranskrip Mahasiswa {student_id}:")
        print(df.to_string(index=False))
    return df
