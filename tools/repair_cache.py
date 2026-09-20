#!/usr/bin/env python3
"""
Tool: Perbaikan Offline Folder Cache Terjemahan (.txt)
Memperbaiki istilah-istilah di file cache yang sudah ada tanpa memanggil API.
"""

import os
import sys
import json
import argparse
from tqdm import tqdm

# Menambahkan parent directory ke sys.path agar bisa import lotm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lotm.post_processor import repair_text


def main():
    parser = argparse.ArgumentParser(description="Perbaiki file cache terjemahan secara offline.")
    parser.add_argument("-d", "--cache-dir", required=True, help="Path ke folder cache berisi file .txt.")
    parser.add_argument("-l", "--log", default="audit_cache_fix.json", help="Path output audit log perbaikan cache.")
    args = parser.parse_args()

    if not os.path.exists(args.cache_dir):
        print(f"❌ Error: Folder cache '{args.cache_dir}' tidak ditemukan.", file=sys.stderr)
        sys.exit(1)

    txt_files = [f for f in os.listdir(args.cache_dir) if f.endswith(".txt")]
    print(f"📁 Memindai {len(txt_files)} file cache di '{args.cache_dir}'...")

    audit_log = []
    fixed_count = 0

    for fname in tqdm(txt_files, desc="Memperbaiki Cache"):
        fpath = os.path.join(args.cache_dir, fname)
        with open(fpath, "r", encoding="utf-8") as fh:
            original = fh.read()

        repaired = repair_text(original, audit_log=audit_log, filename=fname)

        if repaired != original:
            with open(fpath, "w", encoding="utf-8") as fh:
                fh.write(repaired)
            fixed_count += 1

    print(f"\n✅ Selesai! {fixed_count} dari {len(txt_files)} file cache berhasil diperbaiki.")
    if audit_log:
        with open(args.log, "w", encoding="utf-8") as fh:
            json.dump(audit_log, fh, indent=2, ensure_ascii=False)
        print(f"📄 Log perbaikan dicatat di '{args.log}' ({len(audit_log)} pergantian).")
    else:
        print("🎉 Semua file cache sudah bersih. Tidak ada perbaikan yang diperlukan.")


if __name__ == "__main__":
    main()
