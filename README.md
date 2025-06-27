# Proyek Data Warehouse: Peringkat IPK Mahasiswa

Proyek ini adalah sebuah data warehouse sederhana yang dibangun untuk mengekstrak data transkrip nilai dari file PDF, memuatnya ke dalam database MySQL dengan skema bintang (Star Schema), dan melakukan analisis untuk membuat peringkat IPK mahasiswa.

## Struktur Proyek

```
.
├── transkrip/          # Folder untuk menyimpan semua file PDF transkrip nilai
├── analisis.py         # Skrip untuk analisis data dan perhitungan IPK
├── etl.py              # Skrip untuk proses Extract, Transform, Load (ETL)
├── main.py             # Skrip utama untuk menjalankan seluruh alur kerja
├── README.md           # File ini
├── requirements.txt    # Daftar dependensi Python
└── schema.sql          # Skema database (DDL)
```

## Cara Menjalankan Proyek

Ikuti langkah-langkah berikut untuk menjalankan proyek ini dari awal hingga akhir.

### 1. Persiapan Awal

**a. Kloning atau Unduh Proyek**

Pastikan Anda memiliki semua file dari proyek ini di komputer Anda.

**b. Instal Dependensi**

Buka terminal atau command prompt, navigasikan ke direktori proyek, dan instal semua pustaka Python yang dibutuhkan dengan perintah berikut:

```bash
pip install -r requirements.txt
```

**c. Siapkan Database MySQL**

*   Pastikan Anda memiliki server MySQL yang sedang berjalan (misalnya dari XAMPP, WAMP, atau instalasi mandiri).
*   Buat sebuah database baru (misalnya, dengan nama `kampus_dw`).
*   Jalankan query DDL yang ada di dalam file `schema.sql` untuk membuat tabel-tabel yang diperlukan. Anda bisa menggunakan command line `mysql` atau alat bantu GUI seperti phpMyAdmin atau DBeaver.

    ```bash
    mysql -u username -p nama_database_anda < schema.sql
    ```

### 2. Konfigurasi

**a. Letakkan File Transkrip**

Letakkan semua file transkrip nilai dalam format `.pdf` ke dalam folder `transkrip/`.

**b. Atur Koneksi Database**

Buka file `main.py` dan sesuaikan detail koneksi pada dictionary `DB_PARAMS`:

```python
# Ganti dengan detail koneksi database MySQL Anda.
DB_PARAMS = {
    'database': 'nama_database_anda', # Ganti dengan nama database Anda
    'user': 'user_anda',           # Ganti dengan username Anda
    'password': 'password_anda',   # Ganti dengan password Anda
    'host': 'localhost',
    'port': '3306'
}
```

**c. (PENTING) Sesuaikan Pola Ekstraksi Data**

Struktur teks dalam setiap file PDF bisa berbeda. Buka file `etl.py` dan perhatikan fungsi `transform_data`. Pola *regular expression* (regex) telah disesuaikan untuk format transkrip yang lebih spesifik.

## Pola Ekstraksi Data
- Ekstrak NRP/NIM dan Nama mahasiswa dengan regex:
  ```python
  nrp_nama_match = re.search(
      r'NRP\s*/\s*Nama\s*[:\s]*([0-9]{10})\s*/\s*([^\n]+)',
      full_text
  )
  ```
- Ekstrak Tahun Masuk dari NRP (Angkatan) jika tidak ada field terpisah:
  ```python
  entry_year_from_nim_pattern = re.compile(r'^\d{4}(\d{2})')
  ```
- Ekstrak data mata kuliah dan term dengan pola:
  ```python
  course_code_pattern = re.compile(r'^[A-Z]{2}\d{4,6}$')
  course_term_pattern = re.compile(r'(\d{4})/(Gs|Gn)')  # Contoh: '2023/Gs'
  ```

### 3. Jalankan Proyek

Setelah semua konfigurasi selesai, jalankan skrip utama dari terminal:

```bash
python main.py
```

Skrip akan melakukan:
1. Proses ETL untuk setiap file PDF di folder `transkrip/`.
2. Memuat data ke skema star schema MySQL yang telah dibuat.
3. Analisis data:
   - **Peringkat IPK** mahasiswa.
   - **Tingkat kegagalan** per mata kuliah (persentase nilai 'E').
   - **Contoh transkrip** mahasiswa berdasarkan NRP.

### Contoh Output

```text
Memulai proses ETL...
... (log ETL) ...

Memulai proses analisis IPK...
Peringkat IPK Mahasiswa
------------------------
1. Budi Santoso: 3.85
2. Ani Lestari: 3.72
...

Tingkat Kegagalan Mata Kuliah (% nilai E):
Matematika             1.25%
Pemrograman Dasar      0.00%
...

Transkrip Mahasiswa 5026231156:
NRP   : 5026231156
Nama  : Budi Santoso
Semester            Mata Kuliah                 SKS  Nilai  Bobot
Gasal 2023/2024     Pemrograman Dasar            3    A      12.00
Genap 2023/2024     Algoritma dan Struktur Data  4    B      12.00
...
```

## 4. Fitur Tambahan
- **Failure Rate**: hitung persentase mahasiswa yang mendapat nilai 'E' pada setiap mata kuliah.
- **Student Transcript**: tampilkan seluruh riwayat kuliah mahasiswa tertentu berdasarkan NRP.

## Pilihan Teknologi

*   **Database**: Proyek ini menggunakan **MySQL**, sebuah sistem database relasional yang populer dan banyak digunakan, terutama dalam ekosistem web. Jika Anda menginginkan solusi yang lebih sederhana tanpa perlu instalasi server, Anda bisa menggantinya dengan **SQLite**. Untuk itu, Anda perlu mengubah `mysql-connector-python` menjadi `sqlite3` di `requirements.txt` dan menyesuaikan kode koneksi database di `etl.py` dan `analisis.py`.
