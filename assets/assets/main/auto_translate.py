"""
HUONG DAN CHAY TRONG VSCODE
============================
1. Mo Terminal trong VSCode: Ctrl + `
2. Cai thu vien:  python -m pip install deep-translator
3. Chay:          python auto_translate.py
4. Doi ~5-10 phut, file index_vi.js se duoc tao ra
   (khong can API key, hoan toan mien phi!)
"""

import json, time, re, os

INPUT_JS      = "index.js"
OUTPUT_JS     = "index_vi.js"
PROGRESS_FILE = "translate_progress.json"
BATCH_SIZE    = 30   # Google Translate gioi han do dai, de nho hon
DELAY_SECONDS = 1

# ---- Kiem tra thu vien ----
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Dang cai thu vien...")
    os.system("python -m pip install deep-translator")
    from deep_translator import GoogleTranslator

translator = GoogleTranslator(source="zh-CN", target="vi")


def extract_chinese_strings(content):
    pattern = r'"([^"\n]*[\u4e00-\u9fff][^"\n]*)"'
    matches = re.findall(pattern, content)
    filtered = []
    for s in set(matches):
        s = s.strip()
        if len(s) < 2 or len(s) > 80:
            continue
        if s.count('/') > 2 or s.count('\\') > 2:
            continue
        filtered.append(s)
    return sorted(filtered)


def translate_batch(keys):
    """Dich tung chuoi, gop lai thanh dict"""
    results = {}
    for zh in keys:
        try:
            vi = translator.translate(zh)
            results[zh] = vi if vi else zh
        except Exception:
            results[zh] = zh
    return results


def main():
    if not os.path.exists(INPUT_JS):
        print(f"[LOI] Khong tim thay '{INPUT_JS}'")
        print(f"      Chay script nay trong cung thu muc voi index.js")
        return

    print(f"[1/3] Doc file {INPUT_JS}...")
    with open(INPUT_JS, "r", encoding="utf-8") as f:
        content = f.read()

    all_strings = extract_chinese_strings(content)
    print(f"      Tim thay {len(all_strings)} chuoi tieng Trung")

    # Load tien do cu
    translations = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            translations = json.load(f)
        print(f"      Tiep tuc tu lan truoc: {len(translations)} chuoi da dich")

    todo = [s for s in all_strings if s not in translations]
    print(f"      Can dich them: {len(todo)} chuoi\n")

    if todo:
        batches = [todo[i:i+BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
        total = len(batches)
        print(f"[2/3] Dich {len(todo)} chuoi ({total} batch)...")
        print(f"      Uoc tinh: {total * DELAY_SECONDS // 60 + 1}-{total * 2 // 60 + 1} phut\n")

        for i, batch in enumerate(batches, 1):
            print(f"      Batch {i:>3}/{total} ... ", end="", flush=True)
            try:
                result = translate_batch(batch)
                ok = sum(1 for zh, vi in result.items() if vi != zh)
                translations.update(result)
                print(f"OK ({ok}/{len(batch)})")
            except Exception as e:
                print(f"LOI - {e}")
                for zh in batch:
                    if zh not in translations:
                        translations[zh] = zh

            # Luu tien do sau moi batch
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)

            if i < total:
                time.sleep(DELAY_SECONDS)

    # Apply vao file JS
    print(f"\n[3/3] Ghi file {OUTPUT_JS}...")
    new_content = content
    replaced = 0

    for zh, vi in sorted(translations.items(), key=lambda x: len(x[0]), reverse=True):
        if zh == vi or not vi:
            continue
        old = f'"{zh}"'
        new = f'"{vi}"'
        if old in new_content:
            new_content = new_content.replace(old, new)
            replaced += 1

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n========== HOAN THANH ==========")
    print(f"  Da thay the  : {replaced} chuoi")
    print(f"  File output  : {OUTPUT_JS}")
    print(f"  File tien do : {PROGRESS_FILE}")
    print(f"================================")


if __name__ == "__main__":
    main()