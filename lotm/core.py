import os
from typing import Optional
from dotenv import load_dotenv
from tqdm import tqdm
from epub_translator import LLM, translate, SubmitKind

from .config import load_glossary_terms, build_translation_prompt
from .post_processor import repair_epub_file

# Muat variabel lingkungan dari .env jika ada
load_dotenv()


def get_llm_instance(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    cache_path: str = "./cache_lotm"
) -> LLM:
    """
    Menginisialisasi objek LLM dengan kredensial dari environment atau parameter.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Kunci API Gemini tidak ditemukan!\n"
            "Silakan buat file '.env' berisi:\n"
            "GEMINI_API_KEY=AIzaSy...\n"
            "atau set environment variable GEMINI_API_KEY."
        )

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    temp = temperature if temperature is not None else float(os.getenv("GEMINI_TEMPERATURE", "0.15"))

    print(f"[ENGINE] Menginisialisasi Gemini API ({model_name}, temp={temp})")
    print(f"[CACHE] Menggunakan folder cache: {cache_path}")

    return LLM(
        key=key,
        url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model=model_name,
        token_encoding="cl100k_base",
        temperature=temp,
        cache_path=cache_path
    )


def translate_lotm_epub(
    source_epub: str,
    target_epub: str,
    glossary_path: str = "glossaries/glossary_lotm.json",
    cache_dir: str = "./cache_lotm",
    concurrency: int = 3,
    temperature: float = 0.15,
    model: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    audit_log_path: Optional[str] = "audit_report.json",
    skip_post_process: bool = False
):
    """
    Pipeline lengkap penerjemahan LOTM EPUB:
    1. Memuat glossary referensi
    2. Menjalankan LLM Translation (Layer 1)
    3. Menjalankan XML AST Post-Processing & Auto-Repair (Layer 2)
    """
    if not os.path.exists(source_epub):
        raise FileNotFoundError(f"File EPUB sumber tidak ditemukan: {source_epub}")

    # 1. Muat Glossary
    glossary_terms = load_glossary_terms(glossary_path)
    if glossary_terms:
        term_count = len([t for t in glossary_terms.split(",") if t.strip()])
        print(f"[INFO] Glossary dimuat dari '{glossary_path}': {term_count} istilah kanonikal.")
    else:
        print(f"[WARN] Glossary '{glossary_path}' tidak ditemukan atau kosong. Menggunakan aturan bawaan.")

    # 2. Bangun Prompt
    prompt = build_translation_prompt(glossary_terms)

    # 3. Setup LLM
    llm = get_llm_instance(
        api_key=api_key,
        model=model,
        temperature=temperature,
        cache_path=cache_dir
    )

    # 4. Progress Bar
    pbar = tqdm(total=100, desc="Translating Novel", unit="%")
    last_progress = [0.0]

    def on_progress(progress: float):
        increment = (progress - last_progress[0]) * 100
        if increment > 0:
            pbar.update(increment)
            last_progress[0] = progress

    print(f"\n[START] Memulai translasi: {source_epub} -> {target_epub}")
    try:
        translate(
            source_path=source_epub,
            target_path=target_epub,
            target_language="Indonesian",
            submit=SubmitKind.REPLACE,
            llm=llm,
            user_prompt=prompt,
            concurrency=concurrency,
            on_progress=on_progress
        )
    finally:
        pbar.close()

    print(f"\n[SUCCESS] Translasi selesai: {target_epub}")

    # 5. Post-Processing & Auto-Repair
    if not skip_post_process:
        print("\n[INFO] Menjalankan Post-Processing Aman (Layer 2 Auto-Repair)...")
        stats = repair_epub_file(
            input_path=target_epub,
            output_path=target_epub,
            audit_log_path=audit_log_path
        )
        print(f"[FINISH] Berhasil membersihkan {stats['documents_scanned']} dokumen.")
        print(f"[FINISH] Total perbaikan istilah otomatis: {stats['repairs_made']}")
    else:
        print("[INFO] Post-processing dilewati (--skip-post-process aktif).")
