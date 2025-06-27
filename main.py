# main.py

import os
# Sesuaikan nama fungsi yang diimpor dari etl
from etl import extract_and_transform, load_data_to_db
from analisis import calculate_gpa, print_gpa_rankings, get_course_failure_rate, get_student_transcript

# --- KONFIGURASI DATABASE ---
DB_PARAMS = {
    'database': 'kampus_dw',
    'user': 'root',
    'password': ',udw;[sddeptf',
    'host': 'localhost',
    'port': '3306'
}

TRANSKRIP_DIR = 'transkrip/'

def main():
    """Fungsi utama untuk menjalankan proses ETL dan analisis."""
    pdf_files = [f for f in os.listdir(TRANSKRIP_DIR) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"Tidak ada file PDF yang ditemukan di folder '{TRANSKRIP_DIR}'.")
        return

    print("Memulai proses ETL...")
    for pdf_file in pdf_files:
        pdf_path = os.path.join(TRANSKRIP_DIR, pdf_file)
        print(f"Memproses file: {os.path.basename(pdf_path)}")
        
        # Langkah 1 & 2 digabung untuk metode ekstraksi yang lebih andal
        df = extract_and_transform(pdf_path)
        
        # Langkah 3: Load
        if not df.empty:
            load_data_to_db(df, DB_PARAMS)
        else:
            print(f"  -> Tidak ada data yang bisa diekstrak dari {os.path.basename(pdf_path)}.")

    print("\nProses ETL selesai.")

    # Analisis
    print("\nMemulai proses analisis IPK...")
    gpa_df = calculate_gpa(DB_PARAMS)
    
    if gpa_df.empty:
        print("Tidak ada data di database untuk dianalisis.")
    else:
        print_gpa_rankings(gpa_df)
    
    # Tambahan analisis: tingkat kegagalan per mata kuliah
    get_course_failure_rate(DB_PARAMS)
    
    # Demo: tampilkan transkrip mahasiswa contoh
    contoh_id = gpa_df['id_mahasiswa'].iloc[0]
    if contoh_id:
        get_student_transcript(DB_PARAMS, contoh_id)
    
    print("Proses analisis selesai.")

if __name__ == '__main__':
    main()