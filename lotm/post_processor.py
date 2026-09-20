import json
import os
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, NavigableString
import ebooklib
from ebooklib import epub
from tqdm import tqdm

from .config import (
    NORMALIZATION_RULES,
    SORTED_UNAMBIGUOUS_REPAIRS,
    CONTEXTUAL_TITLE_RULES,
)


def repair_text(text: str, audit_log: Optional[List[Dict]] = None, filename: str = "") -> str:
    """
    Melakukan sanitasi teks:
    1. Normalisasi urutan/sequence
    2. Perbaikan istilah unambiguous (diurutkan longest-first)
    3. Perbaikan kontekstual untuk kata umum/gelar tarot
    """
    if not text or not text.strip():
        return text

    original_text = text

    # 1. Normalisasi aturan dasar
    for pattern, replacement in NORMALIZATION_RULES:
        text = pattern.sub(replacement, text)

    # 2. Perbaikan Unambiguous Terms (Longest First)
    for wrong, correct in SORTED_UNAMBIGUOUS_REPAIRS:
        pattern = re.compile(rf"\b{wrong}\b", re.IGNORECASE)
        if pattern.search(text):
            if audit_log is not None:
                audit_log.append({
                    "file": filename,
                    "type": "UNAMBIGUOUS_REPAIR",
                    "original": wrong,
                    "replaced_with": correct,
                    "snippet": text[:80] + "..." if len(text) > 80 else text
                })
            text = pattern.sub(correct, text)

    # 3. Perbaikan Contextual Title Rules
    for pattern, replacement in CONTEXTUAL_TITLE_RULES:
        if pattern.search(text):
            if audit_log is not None:
                audit_log.append({
                    "file": filename,
                    "type": "CONTEXTUAL_REPAIR",
                    "pattern": pattern.pattern,
                    "replaced_with": replacement,
                    "snippet": text[:80] + "..." if len(text) > 80 else text
                })
            text = pattern.sub(replacement, text)

    return text


def process_xhtml_preserve_style(
    xhtml: str,
    audit_log: Optional[List[Dict]] = None,
    filename: str = ""
) -> str:
    """
    Memproses dokumen XHTML secara aman:
    Hanya mengganti isi node NavigableString, melewati tag <style>, <script>, dan <head>.
    Menjamin 100% struktur XML dan styling buku tidak rusak.
    """
    soup = BeautifulSoup(xhtml, "lxml-xml")

    for node in soup.descendants:
        if isinstance(node, NavigableString):
            content = str(node)
            if not content.strip():
                continue

            # Abaikan metadata dan kode stylesheet
            if node.parent and node.parent.name in ("style", "script", "head", "title"):
                continue

            repaired = repair_text(content, audit_log=audit_log, filename=filename)
            if repaired != content:
                node.replace_with(repaired)

    return str(soup)


def repair_epub_file(
    input_path: str,
    output_path: Optional[str] = None,
    audit_log_path: Optional[str] = None
) -> Dict[str, any]:
    """
    Memindai dan memperbaiki file EPUB secara utuh (offline).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File EPUB input tidak ditemukan: {input_path}")

    target_output = output_path or input_path
    print(f"\n[INFO] Membaca EPUB: {input_path}")
    book = epub.read_epub(input_path)

    audit_log: List[Dict] = []
    scanned_pages = 0

    items = [it for it in book.get_items() if it.get_type() == ebooklib.ITEM_DOCUMENT]

    for item in tqdm(items, desc="Post-processing XHTML"):
        filename = item.get_name()
        try:
            raw_content = item.get_content().decode("utf-8")
            clean_content = process_xhtml_preserve_style(
                raw_content,
                audit_log=audit_log,
                filename=filename
            )
            item.set_content(clean_content.encode("utf-8"))
            scanned_pages += 1
        except Exception as e:
            print(f"\n[WARN] Melewati halaman {filename} karena error: {e}")

    print(f"[INFO] Menyimpan EPUB hasil perbaikan ke: {target_output}")
    epub.write_epub(target_output, book)

    if audit_log_path:
        with open(audit_log_path, "w", encoding="utf-8") as f:
            json.dump(audit_log, f, indent=2, ensure_ascii=False)
        print(f"[AUDIT] {len(audit_log)} perbaikan dicatat di '{audit_log_path}'")

    return {
        "documents_scanned": scanned_pages,
        "repairs_made": len(audit_log),
        "output_file": target_output
    }
