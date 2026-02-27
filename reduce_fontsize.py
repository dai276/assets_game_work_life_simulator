"""
HUONG DAN:
1. Dat file nay vao thu muc goc project (cung cap voi thu muc assets/)
2. Mo Terminal: Ctrl + `
3. Chay: python reduce_fontsize.py
   Script se giam _fontSize 30% trong tat ca file JSON trong import/
"""

import json, re, os, shutil
from pathlib import Path

# ==========================================
IMPORT_DIR  = "assets/assets/resources/import"
REDUCE_PERCENT = 30   # giam bao nhieu %
MIN_FONTSIZE   = 12   # kich thuoc nho nhat cho phep (khong giam duoi muc nay)
# ==========================================

def reduce_fontsize(data, count):
    """De quy giam _fontSize trong JSON"""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "_fontSize" and isinstance(value, (int, float)):
                old = value
                new = max(MIN_FONTSIZE, round(value * (1 - REDUCE_PERCENT / 100)))
                data[key] = new
                if old != new:
                    count[0] += 1
            else:
                reduce_fontsize(value, count)
    elif isinstance(data, list):
        for item in data:
            reduce_fontsize(item, count)
    return data


def process_json_files(directory):
    path = Path(directory)
    if not path.exists():
        print(f"[LOI] Khong tim thay thu muc: {directory}")
        return

    all_files = list(path.rglob("*.json"))
    print(f"  Tim thay {len(all_files)} file JSON")

    changed_files = 0
    total_changes = 0

    for filepath in all_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            # Bo qua file khong co _fontSize
            if "_fontSize" not in content:
                continue

            data = json.loads(content)
            count = [0]
            reduce_fontsize(data, count)

            if count[0] > 0:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                changed_files += 1
                total_changes += count[0]
                print(f"  OK: {filepath.name} ({count[0]} font size da giam)")

        except Exception as e:
            print(f"  [skip] {filepath.name}: {e}")

    return changed_files, total_changes


def main():
    print(f"Giam fontSize {REDUCE_PERCENT}% (toi thieu {MIN_FONTSIZE}px)\n")

    # Backup truoc khi sua
    backup_dir = "fontsize_backup"
    if not os.path.exists(backup_dir):
        print(f"[1/2] Tao backup tai {backup_dir}/...")
        shutil.copytree(IMPORT_DIR, backup_dir)
        print(f"      Backup xong!\n")
    else:
        print(f"[1/2] Backup da co san tai {backup_dir}/\n")

    # Xu ly import/
    print(f"[2/2] Xu ly {IMPORT_DIR}...")
    changed, total = process_json_files(IMPORT_DIR)

    print(f"\n========== HOAN THANH ==========")
    print(f"  Da sua  : {changed} file")
    print(f"  Tong    : {total} gia tri fontSize da giam {REDUCE_PERCENT}%")
    print(f"  Backup  : {backup_dir}/")
    print(f"  Khoi phuc: xoa {IMPORT_DIR} roi copy {backup_dir} vao")
    print(f"================================")


if __name__ == "__main__":
    main()