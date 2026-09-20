import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lotm.post_processor import repair_text


def test_longest_first_collision_prevention():
    """
    Memastikan frasa majemuk (compound phrases) tidak terpotong oleh kata tunggal pendek.
    """
    # 1. 'Dunia Roh' harus menjadi 'Spirit World', BUKAN 'The World Roh'
    text1 = "Klein melangkah masuk ke dalam Dunia Roh untuk mencari petunjuk."
    res1 = repair_text(text1)
    assert "Spirit World" in res1
    assert "The World Roh" not in res1

    # 2. 'Jalur Pelaut' harus menjadi 'Sailor Pathway', BUKAN 'Jalur Sailor'
    text2 = "Dia memilih Jalur Pelaut sebagai jalurnya."
    res2 = repair_text(text2)
    assert "Sailor Pathway" in res2
    assert "Jalur Sailor" not in res2

    # 3. 'Laksamana Darah' harus menjadi 'Admiral of Blood'
    text3 = "Kapal milik Laksamana Darah terlihat di cakrawala."
    res3 = repair_text(text3)
    assert "Admiral of Blood" in res3

    # 4. 'Sekte Iblis Wanita' harus menjadi 'Demoness Sect'
    text4 = "Mereka adalah musuh dari Sekte Iblis Wanita."
    res4 = repair_text(text4)
    assert "Demoness Sect" in res4


def test_narrative_words_not_falsely_replaced():
    """
    Memastikan kata umum bahasa Indonesia dalam narasi biasa TIDAK tertukar menjadi istilah Tarot.
    """
    # 'dunia' dalam kalimat narasi biasa harus tetap 'dunia'
    text1 = "Di seluruh penjuru dunia ini, kedamaian hanyalah ilusi semata."
    res1 = repair_text(text1)
    assert "dunia" in res1
    assert "The World" not in res1

    # 'bulan' sebagai penunjuk waktu harus tetap 'bulan'
    text2 = "Tiga bulan kemudian, ekspedisi tersebut akhirnya kembali."
    res2 = repair_text(text2)
    assert "bulan" in res2
    assert "The Moon" not in res2

    # 'bintang' di langit malam harus tetap 'bintang'
    text3 = "Langit malam dihiasi ribuan bintang yang berkilau indah."
    res3 = repair_text(text3)
    assert "bintang" in res3
    assert "The Star" not in res3

    # 'matahari' sebagai benda langit harus tetap 'matahari'
    text4 = "Sinar terik matahari pagi menembus celah jendela kamarnya."
    res4 = repair_text(text4)
    assert "matahari" in res4
    assert "The Sun" not in res4

    # 'hakim' di pengadilan biasa harus tetap 'hakim'
    text5 = "Seorang hakim di pengadilan distrik mengetuk palunya dengan tegas."
    res5 = repair_text(text5)
    assert "hakim" in res5
    assert "Judge" not in res5


def test_contextual_tarot_titles_replaced_correctly():
    """
    Memastikan gelar Tarot yang didahului 'Sang/Si/Kartu' diganti dengan benar.
    """
    text1 = "Sang Dunia membungkuk hormat kepada Sang Bodoh di atas kabut abu-abu."
    res1 = repair_text(text1)
    assert "The World" in res1
    assert "The Fool" in res1
    assert "Gray Fog" in res1

    text2 = "Nona Keadilan menatap Sang Bulan dan Sang Bintang."
    res2 = repair_text(text2)
    assert "Miss Justice" in res2
    assert "The Moon" in res2
    assert "The Star" in res2

    text3 = "Dia memegang Kartu Dunia dan Kartu Matahari."
    res3 = repair_text(text3)
    assert "Kartu The World" in res3
    assert "Kartu The Sun" in res3


def test_sequence_job_normalization():
    """
    Memastikan nama job dalam urutan beyonder tetap dipertahankan dalam bahasa Inggris.
    """
    text1 = "Klein sekarang adalah Urutan 9 Pelihat dan berencana maju ke Urutan 8 Badut."
    res1 = repair_text(text1)
    assert "Urutan 9 Seer" in res1
    assert "Urutan 8 Clown" in res1

    text2 = "Musuhnya adalah seorang Sequence 7 Magician."
    res2 = repair_text(text2)
    assert "Urutan 7 Magician" in res2


def test_unambiguous_terms_repair():
    """
    Memastikan istilah proper noun khas LOTM diperbaiki secara akurat.
    """
    text = "Anggota Elang Malam membawa Artefak Tersegel Tingkat 1 untuk menghadapi Ordo Aurora."
    res = repair_text(text)
    assert "Nighthawks" in res
    assert "Sealed Artifact" in res
    assert "Aurora Order" in res
