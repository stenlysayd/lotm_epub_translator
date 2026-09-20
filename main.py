#!/usr/bin/env python3
"""
LOTM EPUB Translator - Main CLI Interface
=========================================
Penerjemah novel 'Lord of the Mysteries' dengan pertahanan dua lapis:
1. Contextual AI Translation (Gemini API)
2. Deterministic AST XML Post-Processor & Auto-Repair

Usage:
  python main.py -i input.epub -o output.epub
  python main.py -i translated.epub --repair-only
"""

import argparse
import sys
import os

from lotm.core import translate_lotm_epub
from lotm.post_processor import repair_epub_file


def parse_args():
    parser = argparse.ArgumentParser(
        description="Penerjemah EPUB 'Lord of the Mysteries' Profesional (Inggris -> Indonesia)"
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path ke file EPUB sumber (Bahasa Inggris atau EPUB yang ingin diperbaiki)."
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path ke file EPUB hasil terjemahan. (Opsional jika menggunakan --repair-only)."
    )
    parser.add_argument(
        "-g", "--glossary",
        default="glossaries/glossary_lotm.json",
        help="Path ke file JSON glossary istilah kanonikal (default: glossaries/glossary_lotm.json)."
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=3,
        help="Jumlah thread pekerja paralel (default: 3)."
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.15,
        help="Suhu generasi LLM (default: 0.15 agar deterministik dan patuh aturan)."
    )
    parser.add_argument(
        "-m", "--model",
        default="gemini-2.5-flash",
        help="Model Gemini yang digunakan (default: gemini-2.5-flash)."
    )
    parser.add_argument(
        "--cache-dir",
        default="./cache_lotm",
        help="Folder penyimpanan cache terjemahan untuk resume otomatis (default: ./cache_lotm)."
    )
    parser.add_argument(
        "--repair-only",
        action="store_true",
        help="Hanya jalankan Layer 2 (Post-Processing & Auto-Repair) tanpa memanggil API LLM."
    )
    parser.add_argument(
        "--skip-post-process",
        action="store_true",
        help="Lewati tahap Layer 2 (Post-processing XML auto-repair)."
    )
    parser.add_argument(
        "--audit-log",
        default="audit_report.json",
        help="Path output file audit log perbaikan istilah (default: audit_report.json)."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Kunci API Gemini (jika tidak diset melalui file .env)."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Error: File input tidak ditemukan di '{args.input}'", file=sys.stderr)
        sys.exit(1)

    if args.repair_only:
        output_file = args.output or args.input
        print(f"🔧 Mode: REPAIR ONLY")
        print(f"📄 Target EPUB: {args.input} -> {output_file}")
        try:
            stats = repair_epub_file(
                input_path=args.input,
                output_path=output_file,
                audit_log_path=args.audit_log
            )
            print(f"\n✅ Selesai! Berhasil memindai {stats['documents_scanned']} dokumen.")
            print(f"✅ Total istilah diperbaiki: {stats['repairs_made']}")
            print(f"📁 Hasil tersimpan di: {stats['output_file']}")
        except Exception as e:
            print(f"❌ Terjadi kesalahan saat repair: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Mode Translasi Penuh
    if not args.output:
        print("❌ Error: Argumen -o / --output wajib diisi untuk translasi penuh.", file=sys.stderr)
        sys.exit(1)

    try:
        translate_lotm_epub(
            source_epub=args.input,
            target_epub=args.output,
            glossary_path=args.glossary,
            cache_dir=args.cache_dir,
            concurrency=args.concurrency,
            temperature=args.temperature,
            model=args.model,
            api_key=args.api_key,
            audit_log_path=args.audit_log,
            skip_post_process=args.skip_post_process
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Proses dihentikan oleh pengguna. Cache tersimpan dengan aman.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Terjadi kesalahan: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
