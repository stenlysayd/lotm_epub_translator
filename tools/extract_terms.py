#!/usr/bin/env python3
"""
Tool: Ekstraksi Entitas & Istilah Otomatis dari Novel EPUB
Menggunakan LLM dengan dukungan checkpointing dan perbaikan format JSON otomatis.
"""

import os
import sys
import json
import time
import argparse
from collections import Counter
from typing import Dict, List
from dotenv import load_dotenv
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from openai import OpenAI
from tqdm import tqdm
from json_repair import loads as json_repair_loads

load_dotenv()

EXPECTED_KEYS = {
    "people", "organizations", "locations", "artifacts",
    "skills", "pathways", "sequences", "rituals",
    "tarot_aliases", "deities", "epochs_eras", "terminology"
}


def extract_text_from_epub(epub_path: str) -> List[str]:
    book = epub.read_epub(epub_path)
    texts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n")
            if len(text) > 500:
                texts.append(text)
    return texts


def analyze_chunk(client: OpenAI, model: str, text: str, chunk_size: int = 6000) -> Dict[str, List[str]]:
    prompt = """
Return ONLY valid JSON.
Extract all proper nouns and specific terms from this novel excerpt.
Categories:
{
  "people": [],
  "organizations": [],
  "locations": [],
  "artifacts": [],
  "skills": [],
  "pathways": [],
  "sequences": [],
  "rituals": [],
  "tarot_aliases": [],
  "deities": [],
  "epochs_eras": [],
  "terminology": []
}
Rules:
- Original English only
- No translation
- If unsure, omit
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You extract entities and output JSON only."},
            {"role": "user", "content": f"{prompt}\n\nTEXT:\n{text[:chunk_size]}"}
        ],
        temperature=0.0
    )

    content = response.choices[0].message.content
    try:
        data = json_repair_loads(content)
        if isinstance(data, str):
            data = json_repair_loads(data)
        if not isinstance(data, dict):
            return {k: [] for k in EXPECTED_KEYS}

        clean = {}
        for k in EXPECTED_KEYS:
            v = data.get(k, [])
            clean[k] = v if isinstance(v, list) else []
        return clean
    except Exception:
        return {k: [] for k in EXPECTED_KEYS}


def main():
    parser = argparse.ArgumentParser(description="Ekstrak istilah Lord of the Mysteries dari file EPUB.")
    parser.add_argument("-i", "--input", required=True, help="Path file EPUB sumber bahasa Inggris.")
    parser.add_argument("-o", "--output", default="extracted_glossary.json", help="Output JSON file.")
    parser.add_argument("-m", "--model", default="llama-3.1-8b-instant", help="Model Groq yang digunakan.")
    parser.add_argument("--step", type=int, default=3, help="Frekuensi chapter yang di-scan (default: tiap 3 chapter).")
    parser.add_argument("--min-freq", type=int, default=2, help="Frekuensi minimal kemunculan istilah untuk disimpan.")
    args = parser.parse_args()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY belum diatur di file .env", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    print(f"📖 Mengekstrak teks dari: {args.input}")
    chapters = extract_text_from_epub(args.input)
    print(f"📄 Ditemukan {len(chapters)} dokumen bab.")

    temp_file = args.output + ".tmp"
    counters = {k: Counter() for k in EXPECTED_KEYS}
    start_index = 0

    if os.path.exists(temp_file):
        with open(temp_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
            start_index = saved.get("index", 0)
            for k in counters:
                counters[k].update(saved.get("data", {}).get(k, []))
        print(f"🔁 Melanjutkan proses dari bab index {start_index}...")

    indices = list(range(start_index, len(chapters), args.step))
    for idx in tqdm(indices, desc="Memindai Entitas"):
        res = analyze_chunk(client, args.model, chapters[idx])
        for cat, items in res.items():
            if cat in counters:
                counters[cat].update([str(x).strip() for x in items if str(x).strip()])

        # Checkpoint
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({
                "index": idx,
                "data": {k: list(v.elements()) for k, v in counters.items()}
            }, f, ensure_ascii=False)

        time.sleep(1.0)

    # Filter istilah
    final_data = {}
    for cat, cnt in counters.items():
        filtered = [term for term, freq in cnt.items() if freq >= args.min_freq]
        final_data[cat] = sorted(filtered)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    if os.path.exists(temp_file):
        os.remove(temp_file)

    print(f"\n✅ Selesai! Glossary tersimpan di '{args.output}'.")
    for k, v in final_data.items():
        print(f"  - {k}: {len(v)} istilah")


if __name__ == "__main__":
    main()
