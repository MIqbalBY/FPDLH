-- Hapus tabel lama jika ada, untuk memastikan skema yang bersih
DROP TABLE IF EXISTS FactEnrollment;
DROP TABLE IF EXISTS FactNilai;
DROP TABLE IF EXISTS DimMahasiswa;
DROP TABLE IF EXISTS DimMataKuliah;
DROP TABLE IF EXISTS DimTerm;
DROP TABLE IF EXISTS DimGrade;

-- Tabel Dimensi: Mahasiswa
-- Diperkaya dengan tahun masuk dan program studi. Menggunakan surrogate key (sk).
CREATE TABLE DimMahasiswa (
    mahasiswa_sk INT AUTO_INCREMENT PRIMARY KEY,
    id_mahasiswa VARCHAR(20) NOT NULL UNIQUE, -- Natural Key
    nama_mahasiswa VARCHAR(255) NOT NULL,
    tahun_masuk INT,
    program_studi VARCHAR(100)
);

-- Tabel Dimensi: Mata Kuliah
-- Diperkaya dengan jenis mata kuliah.
CREATE TABLE DimMataKuliah (
    matakuliah_sk INT AUTO_INCREMENT PRIMARY KEY,
    id_matakuliah VARCHAR(20) NOT NULL UNIQUE, -- Natural Key
    nama_matakuliah VARCHAR(255) NOT NULL,
    jumlah_sks INT NOT NULL,
    jenis_matakuliah VARCHAR(50) -- Contoh: 'Wajib', 'Pilihan'
);

-- Tabel Dimensi: Waktu/Term
-- Dimensi baru untuk analisis tren berdasarkan waktu.
CREATE TABLE DimTerm (
    term_sk INT AUTO_INCREMENT PRIMARY KEY,
    nama_semester VARCHAR(50) NOT NULL UNIQUE, -- Contoh: 'Gasal 2023/2024'
    tahun_akademik INT,
    semester VARCHAR(10) -- Contoh: 'Gasal', 'Genap'
);

-- Tabel Dimensi: Nilai
-- Memisahkan logika penilaian dari kode aplikasi.
CREATE TABLE DimGrade (
    grade_sk INT AUTO_INCREMENT PRIMARY KEY,
    nilai_huruf VARCHAR(5) NOT NULL UNIQUE,
    nilai_angka DECIMAL(3,2) NOT NULL,
    keterangan_lulus BOOLEAN NOT NULL -- 1 untuk Lulus, 0 untuk Tidak Lulus
);

-- Tabel Fakta: Pendaftaran dan Nilai
-- Inti dari star schema, hanya berisi measures dan foreign key ke dimensi.
CREATE TABLE FactEnrollment (
    enrollment_pk INT AUTO_INCREMENT PRIMARY KEY,
    mahasiswa_sk INT,
    matakuliah_sk INT,
    term_sk INT,
    grade_sk INT,
    sks_diambil INT NOT NULL,
    sks_diperoleh INT NOT NULL,
    bobot_nilai DECIMAL(5,2) NOT NULL, -- Hasil dari (nilai_angka * jumlah_sks)

    -- Mencegah entri duplikat untuk mata kuliah yang sama oleh mahasiswa yang sama di term yang sama
    UNIQUE(mahasiswa_sk, matakuliah_sk, term_sk),

    -- Mendefinisikan Foreign Key Constraints
    FOREIGN KEY (mahasiswa_sk) REFERENCES DimMahasiswa(mahasiswa_sk),
    FOREIGN KEY (matakuliah_sk) REFERENCES DimMataKuliah(matakuliah_sk),
    FOREIGN KEY (term_sk) REFERENCES DimTerm(term_sk),
    FOREIGN KEY (grade_sk) REFERENCES DimGrade(grade_sk)
);

-- Isi tabel DimGrade dengan data awal.
INSERT INTO DimGrade (nilai_huruf, nilai_angka, keterangan_lulus) VALUES
('A', 4.0, 1),
('AB', 3.5, 1),
('B', 3.0, 1),
('BC', 2.5, 1),
('C', 2.0, 1),
('D', 1.0, 1),
('E', 0.0, 0);
