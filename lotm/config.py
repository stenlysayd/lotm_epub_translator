import json
import os
import re
from typing import Dict, List, Tuple

# =====================================================================
# 1. NORMALIZATION RULES (MEKANIS / STANDARDISASI AWAL)
# =====================================================================
NORMALIZATION_RULES: List[Tuple[re.Pattern, str]] = [
    # Standardisasi Sequence -> Urutan X
    (re.compile(r"\bSequence\s+(\d+)\b", re.IGNORECASE), r"Urutan \1"),
    # Standardisasi Grade Sealed Artifact -> Tingkat X
    (re.compile(r"\bGrade\s+(\d+)\b", re.IGNORECASE), r"Tingkat \1"),
]

# =====================================================================
# 2. UNAMBIGUOUS AUTO-REPAIR MAP
# Istilah multi-kata atau proper noun unik yang TIDAK AKAN PERNAH
# tertukar dengan bahasa Indonesia sehari-hari.
# CATATAN: Semua entri ini akan diurutkan longest-first agar tidak
# terjadi pemotongan parsial (misal 'Dunia Roh' vs 'Dunia').
# =====================================================================
UNAMBIGUOUS_REPAIR_MAP: Dict[str, str] = {
    # --- A. ORGANISASI & KELOMPOK (Organizations) ---
    r"Klub Tarot": "Tarot Club",
    r"Pertemuan Tarot": "Tarot Gathering",
    r"Elang Malam": "Nighthawks",
    r"Penghukum yang Ditugaskan": "Mandated Punishers",
    r"Penghukum Mandat": "Mandated Punishers",
    r"Sarang Mesin": "Machinery Hivemind",
    r"Pemikiran Mesin": "Machinery Hivemind",
    r"Ordo Aurora": "Aurora Order",
    r"Ordo Pertapa Musa": "Moses Ascetic Order",
    r"Sekolah Pemikiran Mawar": "Rose School of Thought",
    r"Aliran Pemikiran Mawar": "Rose School of Thought",
    r"Penebusan Mawar": "Rose Redemption",
    r"Ordo Hermit Senja": "Twilight Hermit Order",
    r"Ordo Pertapa Senja": "Twilight Hermit Order",
    r"Psikologi Alkemis": "Psychology Alchemists",
    r"Alkemis Psikologi": "Psychology Alchemists",
    r"Episkopat Numinous": "Numinous Episcopate",
    r"Sekte Iblis Wanita": "Demoness Sect",
    r"Sekte Penyihir": "Demoness Sect",
    r"Sekolah Pemikiran Kehidupan": "Life School of Thought",
    r"Gereja Dewi Semalam": "Church of the Evernight Goddess",
    r"Gereja Penguasa Badai": "Church of the Lord of Storms",
    r"Gereja Matahari Berkobar Abadi": "Church of the Eternal Blazing Sun",
    r"Gereja Uap dan Mesin": "Church of Steam and Machinery",
    r"Gereja Ibu Bumi": "Church of Earth Mother",
    r"Gereja Dewa Pertempuran": "Church of the God of Combat",
    r"Kota Perak": "City of Silver",
    r"Keluarga Abraham": "Abraham Family",
    r"Keluarga Antigonus": "Antigonus Family",
    r"Keluarga Zaratul": "Zaratul Family",
    r"Dinasti Tudor": "Tudor Dynasty",
    r"Kekaisaran Trunsoest": "Trunsoest Empire",
    r"Kekaisaran Solomon": "Solomon Empire",
    r"Fajar Elemen": "Element Dawn",
    r"Perkumpulan Riset Babon Berambut Keriting": "Curly-Haired Baboons Research Society",
    r"April Mop": "April Fool's",
    r"Ordo Teosofi": "Theosophy Order",
    r"Pertapa Nasib": "Hermits of Fate",
    r"Dewa Laut": "Sea God",
    r"Pencipta Sejati": "True Creator",
    r"Pencipta Asli": "True Creator",
    r"Salib Besi dan Darah": "Iron and Blood Cross Order",
    r"Ordo Salib Besi dan Darah": "Iron and Blood Cross Order",

    # --- B. PATHWAY & JOB COMPOUND (Multi-kata) ---
    r"Jalur Peramal": "Fool Pathway",
    r"Jalur Pintu": "Door Pathway",
    r"Jalur Kekeliruan": "Error Pathway",
    r"Jalur Visioner": "Visionary Pathway",
    r"Jalur Penonton": "Spectator Pathway",
    r"Jalur Pria Tergantung": "Hanged Man Pathway",
    r"Jalur Matahari": "Sun Pathway",
    r"Jalur Tiran": "Tyrant Pathway",
    r"Jalur Pelaut": "Sailor Pathway",
    r"Jalur Menara Putih": "White Tower Pathway",
    r"Jalur Kegelapan": "Darkness Pathway",
    r"Jalur Kematian": "Death Pathway",
    r"Jalur Raksasa Senja": "Twilight Giant Pathway",
    r"Jalur Pendeta Merah": "Red Priest Pathway",
    r"Jalur Pemburu": "Hunter Pathway",
    r"Jalur Iblis Wanita": "Demoness Pathway",
    r"Jalur Kaisar Hitam": "Black Emperor Pathway",
    r"Jalur Pengacara": "Lawyer Pathway",
    r"Jalur Hakim": "Justiciar Pathway",
    r"Jalur Arbiter": "Arbiter Pathway",
    r"Jalur Roda Keberuntungan": "Wheel of Fortune Pathway",
    r"Jalur Monster": "Monster Pathway",
    r"Jalur Bulan": "Moon Pathway",
    r"Jalur Ibu": "Mother Pathway",
    r"Jalur Penanam": "Planter Pathway",
    r"Jalur Abyss": "Abyss Pathway",
    r"Jalur Terbelenggu": "Chained Pathway",
    r"Jalur Paragon": "Paragon Pathway",
    r"Jalur Petapa": "Hermit Pathway",

    # Istilah Sequence / Job Komposit
    r"Tanpa Wajah": "Faceless",
    r"Penyihir Bizarro": "Bizarro Sorcerer",
    r"Sarjana Masa Lalu": "Scholar of Yore",
    r"Penyeru Keajaiban": "Miracle Invoker",
    r"Pelayan Misteri": "Attendant of Mysteries",
    r"Berjalan dalam Mimpi": "Dream Walker",
    r"Iblis Wanita Kesenangan": "Demoness of Pleasure",
    r"Iblis Wanita Awet Muda": "Demoness of Unaging",
    r"Pendeta Merah": "Red Priest",
    r"Ksatria Berdarah Besi": "Iron-blooded Knight",
    r"Kunci Bintang": "Key of Stars",
    r"Mentor Kebingungan": "Mentor of Confusion",
    r"Cacing Waktu": "Worm of Time",
    r"Pengumpul Mayat": "Corpse Collector",
    r"Penggali Kubur": "Gravedigger",
    r"Medium Roh": "Spirit Medium",
    r"Penjaga Gerbang": "Gatekeeper",
    r"Penyair Tengah Malam": "Midnight Poet",
    r"Penjamin Jiwa": "Soul Assurer",
    r"Penyihir Roh": "Spirit Warlock",
    r"Pengangkut Jenazah": "Ferryman",
    r"Baron Korupsi": "Baron of Corruption",
    r"Mentor Ketidaktertiban": "Mentor of Disorder",
    r"Kaisar Hitam": "Black Emperor",
    r"Orang Beruntung": "Lucky One",
    r"Pendeta Bencana": "Calamity Priest",
    r"Ular Merkuri": "Snake of Mercury",
    r"Pengintai Misteri": "Mystery Pryer",
    r"Sarjana Jarak Dekat": "Melee Scholar",
    r"Profesor Gulungan": "Scroll Professor",

    # Gelar Karakter Komposit
    r"Ular Nasib": "Snake of Fate",
    r"Malaikat Merah": "Red Angel",
    r"Raja Lima Lautan": "King of the Five Seas",
    r"Laksamana Bintang": "Admiral of Stars",
    r"Laksamana Darah": "Admiral of Blood",
    r"Laksamana Neraka": "Admiral Hell Ludwell",

    # --- C. LOKASI (Locations) ---
    r"Kota Tingen": "Tingen City",
    r"Kerajaan Loen": "Loen Kingdom",
    r"Republik Intis": "Intis Republic",
    r"Kekaisaran Feysac": "Feysac Empire",
    r"Kerajaan Feynapotter": "Feynapotter Kingdom",
    r"Kekaisaran Balam": "Balam Empire",
    r"Kepulauan Rorsted": "Rorsted Archipelago",
    r"Pelabuhan Bansy": "Bansy Harbor",
    r"Pulau Oravi": "Oravi Island",
    r"Pulau Pasu": "Pasu Island",
    r"Laut Sonia": "Sonia Sea",
    r"Laut Kabut": "Fog Sea",
    r"Laut Berserk": "Berserk Sea",
    r"Tanah Para Dewa yang Ditinggalkan": "Forsaken Land of God",
    r"Kota Sore": "Afternoon Town",
    r"Kota Bulan": "Moon City",
    r"Pengadilan Raja Raksasa": "Giant King’s Court",
    r"Pegunungan Hornacis": "Hornacis Mountain Range",
    r"Taman Eden": "Garden of Eden",
    r"Perjalanan Groselle": "Groselle’s Travels",
    r"Dunia Roh": "Spirit World",
    r"Dunia Astral": "Astral World",
    r"Kastil Sefirah": "Sefirah Castle",
    r"Kabut Abu-abu": "Gray Fog",

    # --- D. ARTEFAK & ISTILAH TEKNIS (Artifacts / Beyonder Terms) ---
    r"Kartu Penistaan": "Blasphemy Card",
    r"Karakteristik Beyonder": "Beyonder Characteristic",
    r"Formula Ramuan": "Potion Formula",
    r"Kelaparan Merayap": "Creeping Hunger",
    r"Lonceng Kematian": "Death Knell",
    r"Peluit Tembaga Azik": "Azik’s Copper Whistle",
    r"Perjalanan Leymano": "Leymano’s Travels",
    r"Pedang Keadilan": "Sword of Justice",
    r"Buku Kuningan Trunsoest": "Trunsoest Brass Book",
    r"Buku Catatan Keluarga Antigonus": "Antigonus Family's Notebook",
    r"Mata Hitam Semua": "All-Black Eye",
    r"Bros Matahari": "Sun Brooch",
    r"Botol Racun Biologis": "Biological Poison Bottle",
    r"Kunci Utama": "Master Key",
    r"Buku Bencana": "Book of Calamity",
    r"Artefak Tersegel": "Sealed Artifact",
    r"Metode Berakting": "Acting Method",
    r"Penglihatan Roh": "Spirit Vision",
    r"Benang Tubuh Roh": "Spirit Body Threads",
    r"Lepas Kendali": "kehilangan kendali",
    r"Hilang Kendali": "kehilangan kendali",
}

# =====================================================================
# 3. CONTEXTUAL REPAIR RULES (MENGATASI FALSE POSITIVES KATA UMUM)
# Aturan khusus untuk kata-kata bahasa Indonesia sehari-hari seperti:
# 'dunia', 'bulan', 'bintang', 'matahari', 'pria tergantung', dll.
# HANYA diganti jika didahului awalan gelar atau dalam konteks kartu/nama.
# =====================================================================
CONTEXTUAL_TITLE_RULES: List[Tuple[re.Pattern, str]] = [
    # Gelar Tarot dengan prefiks Sang/Si/Tuan/Nona/Kartu
    (re.compile(r"\b(?:Sang|Si)\s+Bodoh\b", re.IGNORECASE), "The Fool"),
    (re.compile(r"\b(?:Sang|Si)\s+Dunia\b", re.IGNORECASE), "The World"),
    (re.compile(r"\bKartu\s+Dunia\b", re.IGNORECASE), "Kartu The World"),
    (re.compile(r"\b(?:Sang|Si)\s+Bulan\b", re.IGNORECASE), "The Moon"),
    (re.compile(r"\bKartu\s+Bulan\b", re.IGNORECASE), "Kartu The Moon"),
    (re.compile(r"\b(?:Sang|Si)\s+Bintang\b", re.IGNORECASE), "The Star"),
    (re.compile(r"\bKartu\s+Bintang\b", re.IGNORECASE), "Kartu The Star"),
    (re.compile(r"\b(?:Sang|Si)\s+Matahari\b", re.IGNORECASE), "The Sun"),
    (re.compile(r"\bKartu\s+Matahari\b", re.IGNORECASE), "Kartu The Sun"),
    (re.compile(r"\b(?:Sang|Si)\s+Pertapa\b", re.IGNORECASE), "The Hermit"),
    (re.compile(r"\bKartu\s+Pertapa\b", re.IGNORECASE), "Kartu The Hermit"),
    (re.compile(r"\b(?:Pria\s+(?:Yang\s+)?Digantung|Pria\s+Tergantung)\b", re.IGNORECASE), "The Hanged Man"),
    (re.compile(r"\b(?:Sang|Nona)\s+Penghakiman\b", re.IGNORECASE), "The Judgement"),
    (re.compile(r"\b(?:Sang|Nona)\s+Keadilan\b", re.IGNORECASE), "Miss Justice"),
    (re.compile(r"\b(?:Sang|Tuan)\s+Pesulap\b", re.IGNORECASE), "The Magician"),
    (re.compile(r"\b(?:Sang|Nona)\s+Penyihir\b", re.IGNORECASE), "The Magician"),

    # Job names hanya ketika didahului "Urutan X" atau "Sequence X"
    (re.compile(r"\b(Urutan\s+\d+)\s+Pelihat\b", re.IGNORECASE), r"\1 Seer"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Badut\b", re.IGNORECASE), r"\1 Clown"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pesulap\b", re.IGNORECASE), r"\1 Magician"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Dalang\b", re.IGNORECASE), r"\1 Marionettist"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Penonton\b", re.IGNORECASE), r"\1 Spectator"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pelaut\b", re.IGNORECASE), r"\1 Sailor"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pemburu\b", re.IGNORECASE), r"\1 Hunter"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pembunuh\b", re.IGNORECASE), r"\1 Assassin"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pengacara\b", re.IGNORECASE), r"\1 Lawyer"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Hakim\b", re.IGNORECASE), r"\1 Judge"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Pemenang\b", re.IGNORECASE), r"\1 Winner"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Penyair\b", re.IGNORECASE), r"\1 Bard"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Hasutan\b", re.IGNORECASE), r"\1 Instigator"),
    (re.compile(r"\b(Urutan\s+\d+)\s+Penyihir\b", re.IGNORECASE), r"\1 Witch"),
]

# Urutkan UNAMBIGUOUS_REPAIR_MAP berdasarkan panjang teks terbesar lebih dahulu
SORTED_UNAMBIGUOUS_REPAIRS = sorted(
    UNAMBIGUOUS_REPAIR_MAP.items(),
    key=lambda x: len(x[0]),
    reverse=True
)


# =====================================================================
# 4. GLOSSARY LOADER & PROMPT BUILDER
# =====================================================================
def load_glossary_terms(file_path: str) -> str:
    """Membaca file JSON glossary dan mengembalikan gabungan string istilah unik."""
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        terms = set()
        for category in data.values():
            if isinstance(category, list):
                for term in category:
                    if isinstance(term, str) and len(term.strip()) >= 3:
                        terms.add(term.strip())
        return ", ".join(sorted(terms))
    except Exception:
        return ""


def build_translation_prompt(glossary_terms: str = "") -> str:
    """Membuat system prompt penerjemahan sastra Lord of the Mysteries."""
    return f"""
PERAN:
Anda adalah penerjemah profesional novel fantasi "Lord of the Mysteries" (Inggris ke Bahasa Indonesia).

[STANDAR GAYA BAHASA]
1. Sastra, misterius, imersif, dan bernuansa Victorian.
2. JANGAN menerjemahkan kata demi kata (harfiah). Gunakan alur bahasa Indonesia yang luwes dan alami.
3. Utamakan kalimat aktif bila kalimat pasif bahasa Inggris terasa kaku dalam bahasa Indonesia.

[ATURAN MUTLAK TERMINOLOGI - PROPER NOUNS]
DILARANG KERAS menerjemahkan Istilah Khusus, Nama Karakter, Tempat, Organisasi, Job/Sequence, dan Artefak.
Biarkan tetap dalam Bahasa Inggris Asli.
Contoh: "Klein Moretti", "The Fool", "The World", "Nighthawks", "Backlund", "Sealed Artifact", "Seer", "Creeping Hunger", "Demoness".

[ATURAN KHUSUS SEQUENCE & PATHWAY]
1. "Sequence X" -> Terjemahkan menjadi "Urutan X" (contoh: Sequence 9 -> Urutan 9).
2. Nama Job setelah Sequence TETAP INGGRIS (contoh: Urutan 9 Seer, Urutan 8 Clown).
3. Nama Pathway ditulis dalam bahasa Inggris diikuti nama Indonesia dalam kurung:
   - Fool Pathway (Jalur Peramal)
   - Door Pathway (Jalur Pintu)
   - Error Pathway (Jalur Kekeliruan)
   - Visionary Pathway (Jalur Visioner)
   - Hanged Man Pathway (Jalur Pria Tergantung)
   - Sun Pathway (Jalur Matahari)
   - Tyrant Pathway (Jalur Tiran)
   - Darkness Pathway (Jalur Kegelapan)
   - Death Pathway (Jalur Kematian)
   - Red Priest Pathway (Jalur Pendeta Merah)
   - Demoness Pathway (Jalur Iblis Wanita)
   - Black Emperor Pathway (Jalur Kaisar Hitam)
   - Justiciar Pathway (Jalur Hakim)
   - Wheel of Fortune Pathway (Jalur Roda Keberuntungan)

[GLOSSARY REFERENSI ISTILAH WAJIB INGGRIS]:
{glossary_terms}

PERINTAH:
Terjemahkan teks berikut ke Bahasa Indonesia dengan memenuhi semua aturan di atas:
""".strip()
