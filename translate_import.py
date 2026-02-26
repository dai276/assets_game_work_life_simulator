
import json, re, os, time, shutil
from pathlib import Path

# ==========================================
IMPORT_DIR    = "assets/assets/resources/import"  # thu muc chua file JSON
BACKUP_DIR    = "import_backup"                    # thu muc backup file goc
PROGRESS_FILE = "translate_import_progress.json"  # luu tien do
DELAY         = 0.5  # giay cho giua moi chuoi (tranh bi block)
# ==========================================

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Dang cai thu vien...")
    os.system("python -m pip install deep-translator")
    from deep_translator import GoogleTranslator

translator = GoogleTranslator(source="zh-CN", target="vi")

def is_chinese(text):
    """Kiem tra chuoi co chua tieng Trung khong"""
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))

def translate_text(text):
    """Dich mot chuoi tieng Trung sang tieng Viet"""
    try:
        result = translator.translate(str(text))
        return result if result else text
    except Exception as e:
        print(f"\n        [warn] Loi dich '{text[:20]}...': {e}")
        return text

def process_value(value, translations_cache):
    """De quy xu ly gia tri JSON - dich tat ca chuoi tieng Trung"""
    if isinstance(value, str):
        if is_chinese(value):
            # Dung cache de khong dich lai chuoi da dich
            if value not in translations_cache:
                translations_cache[value] = translate_text(value)
                time.sleep(DELAY)
            return translations_cache[value]
        return value
    elif isinstance(value, dict):
        return {k: process_value(v, translations_cache) for k, v in value.items()}
    elif isinstance(value, list):
        return [process_value(item, translations_cache) for item in value]
    return value

def find_all_json_files(directory):
    """Tim tat ca file JSON trong thu muc"""
    path = Path(directory)
    if not path.exists():
        return []
    return list(path.rglob("*.json"))

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"translations": {}, "done_files": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def main():
    # Kiem tra thu muc
    if not os.path.exists(IMPORT_DIR):
        print(f"[LOI] Khong tim thay thu muc: {IMPORT_DIR}")
        print(f"      Hay chay script nay o thu muc goc cua project")
        return

    # Tim tat ca file JSON
    all_files = find_all_json_files(IMPORT_DIR)
    # Chi lay file co tiem nang chua tieng Trung (bo qua sprite frame)
    candidate_files = []
    for f in all_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if is_chinese(content) and '"__type__": "cc.SpriteFrame"' not in content:
                candidate_files.append(f)
        except:
            pass

    print(f"[1/3] Quet thu muc {IMPORT_DIR}")
    print(f"      Tong file JSON    : {len(all_files)}")
    print(f"      File co tieng TQ  : {len(candidate_files)}")

    if not candidate_files:
        print("\n      Khong tim thay file nao co tieng Trung!")
        return

    # Load tien do cu
    progress = load_progress()
    translations_cache = progress["translations"]
    done_files = set(progress["done_files"])

    todo_files = [f for f in candidate_files if str(f) not in done_files]
    print(f"      Can xu ly them    : {len(todo_files)} file\n")

    # Backup
    if not os.path.exists(BACKUP_DIR):
        print(f"[2/3] Tao backup tai {BACKUP_DIR}/...")
        for f in candidate_files:
            rel = f.relative_to(IMPORT_DIR)
            backup_path = Path(BACKUP_DIR) / rel
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, backup_path)
        print(f"      Backup xong {len(candidate_files)} file\n")
    else:
        print(f"[2/3] Backup da co san tai {BACKUP_DIR}/\n")

    # Dich
    print(f"[3/3] Bat dau dich {len(todo_files)} file...")
    total = len(todo_files)

    for i, filepath in enumerate(todo_files, 1):
        print(f"\n  File {i}/{total}: {filepath.name}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Dem truoc so chuoi TQ trong file nay
            content_str = json.dumps(data, ensure_ascii=False)
            zh_count = len(re.findall(r'[\u4e00-\u9fff]+', content_str))
            print(f"    {zh_count} ky tu TQ, dang dich...", end="", flush=True)

            # Dich
            translated_data = process_value(data, translations_cache)

            # Ghi lai file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)

            print(f" xong!")

            # Luu tien do
            done_files.add(str(filepath))
            progress["translations"] = translations_cache
            progress["done_files"] = list(done_files)
            save_progress(progress)

        except json.JSONDecodeError:
            print(f"    [skip] Khong phai JSON hop le")
        except Exception as e:
            print(f"    [LOI] {e}")

    print(f"\n========== HOAN THANH ==========")
    print(f"  Da dich   : {len(done_files)} file")
    print(f"  Cache dich : {len(translations_cache)} chuoi")
    print(f"  Backup    : {BACKUP_DIR}/")
    print(f"  Khoi phuc : copy {BACKUP_DIR}/ -> {IMPORT_DIR}/")
    print(f"================================")

if __name__ == "__main__":
    main()