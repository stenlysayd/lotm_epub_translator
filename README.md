# 🔮 Lord of the Mysteries (LOTM) EPUB Translator

Sistem penerjemah novel khusus **"Lord of the Mysteries"** (Bahasa Inggris ke Bahasa Indonesia) berbasis LLM (Google Gemini) dengan **Arsitektur Pertahanan Dua Lapis (Dual-Layer Engine)** untuk menjamin konsistensi istilah kanonikal, gaya sastra alami, dan keutuhan format buku EPUB.

---

## 🌟 Mengapa Tool Ini Dibuat?

Menerjemahkan novel web fantasi seperti *Lord of the Mysteries* menggunakan alat terjemahan standar (Google Translate / DeepL / Prompt LLM biasa) sering kali menghasilkan terjemahan yang rusak:
- **Kerusakan Istilah Kanonikal**: Nama organisasi dan istilah sakral diterjemahkan secara harfiah (misal *"Nighthawks"* menjadi *"Elang Malam"*, *"Tarot Club"* menjadi *"Klub Tarot"*, atau *"Sealed Artifact"* menjadi *"Artefak Tersegel"*).
- **Kerusakan Tag & Styling EPUB**: Penggantian regex teks biasa (*raw string replace*) dapat merusak tag XML, atribut CSS, dan struktur layout buku.
- **Masalah Ambiguitas Kata Umum**: Skrip otomatis biasa sering mengganti kata umum bahasa Indonesia (misal *"dunia"*, *"bulan"*, *"bintang"*, *"matahari"*) menjadi nama kartu Tarot (*"The World"*, *"The Moon"*, dll), sehingga merusak alur kalimat cerita.

**LOTM EPUB Translator** memecahkan masalah tersebut dengan arsitektur dua lapis.

---

## 🛡️ Arsitektur Dua Lapis (Dual-Layer Engine)

```
[EPUB Bahasa Inggris]
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Contextual AI Translation (Gemini Flash)           │
│ - Prompt sastra imersif Victorian                           │
│ - Injeksi dataset glossary kanonikal (glossaries/lotm.json) │
│ - Caching per-paragraf & resume otomatis                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Deterministic AST XML Post-Processor & Auto-Repair │
│ - Membedah DOM XHTML dengan BeautifulSoup (lxml-xml)        │
│ - Hanya menargetkan NavigableString (CSS/style/tag aman)     │
│ - Longest-First Regex: Mencegah pemotongan frasa majemuk    │
│ - Contextual Title Filter: Membedakan kata umum vs persona  │
│ - Audit logging lengkap (audit_report.json)                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
[EPUB Bahasa Indonesia Bersih & Rapi]
```

---

## 📁 Struktur Repositori

```text
lotm_epub_translator/
├── .env.example              # Template konfigurasi environment
├── .gitignore                # Filter file rahasia, cache, dan epub besar
├── requirements.txt          # Daftar dependensi Python
├── README.md                 # Dokumentasi ini
├── main.py                   # Entrypoint CLI utama
├── lotm/
│   ├── __init__.py
│   ├── config.py             # Aturan normalisasi, longest-first mapping, dan prompt
│   ├── core.py               # Inisialisasi LLM dan orkestrasi pipeline
│   └── post_processor.py     # Parser XML DOM aman dan engine auto-repair
├── glossaries/
│   └── glossary_lotm.json    # Database istilah kanonikal Lord of the Mysteries
├── tools/
│   ├── __init__.py
│   ├── extract_terms.py      # Tool ekstraksi istilah otomatis untuk volume baru
│   └── repair_cache.py       # Tool perbaikan file cache terjemahan offline
└── tests/
    └── test_repair.py        # Unit test verifikasi logika perbaikan
```

---

## 🚀 Panduan Instalasi

### 1. Kloning & Masuk ke Folder
```bash
git clone https://github.com/stenlysayd/lotm_epub_translator.git
cd lotm_epub_translator
```

### 2. Pasang Dependensi
Pastikan Anda menggunakan Python 3.10+:
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi API Key
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Buka `.env` dan masukkan API Key Gemini Anda:
```env
GEMINI_API_KEY=AIzaSy...
```

---

## 📖 Cara Penggunaan

### 1. Penerjemahan Penuh (Full Pipeline)
Menerjemahkan novel dari awal sampai selesai dengan post-processing otomatis:
```bash
python main.py -i "input_novel.epub" -o "novel_terjemahan_indo.epub"
```

Opsi tambahan:
```bash
python main.py -i "input.epub" -o "output.epub" -c 5 -t 0.15 --model gemini-2.5-flash
```
- `-c, --concurrency`: Jumlah thread bersamaan (default: 3).
- `-t, --temperature`: Suhu generasi (default: 0.15 untuk kepatuhan maksimal).
- `--cache-dir`: Folder cache progress (default: `./cache_lotm`).

### 2. Mode Perbaikan Saja (Offline Repair Mode)
Jika Anda sudah memiliki file EPUB terjemahan tetapi banyak istilah yang bocor/salah, Anda dapat memperbaikinya **secara offline tanpa menggunakan kuota API**:
```bash
python main.py -i "novel_terjemahan_lama.epub" -o "novel_terjemahan_repaired.epub" --repair-only
```

### 3. Ekstraksi Istilah Otomatis untuk Volume Baru (`tools/extract_terms.py`)
Mengekstrak entitas dan proper nouns dari buku bahasa Inggris untuk memperkaya glossary:
```bash
python tools/extract_terms.py -i "lord_of_mysteries_volume_5.epub" -o "glossaries/glossary_vol5.json"
```

### 4. Perbaikan File Cache Terjemahan Offline (`tools/repair_cache.py`)
Memperbaiki istilah pada file `.txt` di folder cache tanpa menerjemahkan ulang:
```bash
python tools/repair_cache.py -d "./cache_lotm"
```

---

## 🧪 Menjalankan Unit Test

Untuk memverifikasi keakuratan regex collision, penanganan kata ambigu, dan pemrosesan urutan sequence:
```bash
pytest tests/test_repair.py -v
```

---

## ⚖️ Lisensi & Penghargaan
- Dibuat untuk komunitas pembaca novel *Lord of the Mysteries* (Cuttlefish That Loves Diving).
- Menggunakan pustaka pendukung `epub-translator`, `beautifulsoup4`, dan `lxml`.
