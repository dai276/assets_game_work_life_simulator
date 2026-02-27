"""
Script inject hook dich tu dong vao index.js
--------------------------------------------
HUONG DAN:
1. Dat file nay cung thu muc voi index.js
2. Chay: python inject_hook.py
3. Ket qua: index.js duoc them hook o cuoi file
   - Tu dong dich tieng Trung -> Viet khi game hien thi text
   - Thu nho font 30% cho text tieng Viet
   - Cache ket qua dich vao localStorage (offline lan sau)
   - Goi Google Translate neu chua co trong cache (can mang)
"""

import os, shutil

INPUT_JS  = "index.js"
BACKUP_JS = "index_before_hook.js"

# =============================================
# Doan hook se duoc nhem vao cuoi index.js
# =============================================
HOOK_CODE = r"""

// ============================================
// VI HOA HOOK - Tu dong dich Trung -> Viet
// ============================================
(function() {
    'use strict';

    var FONT_SCALE    = 0.7;   // thu nho 30%
    var MIN_FONT      = 12;    // font nho nhat
    var CACHE_KEY     = 'vi_dict_cache';
    var BATCH_DELAY   = 100;   // ms cho giua cac request dich
    var pendingQueue  = [];    // hang doi cho dich
    var isTranslating = false;

    // --- Load cache tu localStorage ---
    var viDict = {};
    try {
        var saved = localStorage.getItem(CACHE_KEY);
        if (saved) viDict = JSON.parse(saved) || {};
    } catch(e) {}

    // --- Luu cache ---
    function saveCache() {
        try {
            localStorage.setItem(CACHE_KEY, JSON.stringify(viDict));
        } catch(e) {}
    }

    // --- Kiem tra co tieng Trung khong ---
    function isChinese(text) {
        return typeof text === 'string' && /[\u4e00-\u9fff]/.test(text);
    }

    // --- Goi Google Translate ---
    function googleTranslate(text, callback) {
        try {
            var url = 'https://translate.googleapis.com/translate_a/single'
                + '?client=gtx&sl=zh-CN&tl=vi&dt=t&q='
                + encodeURIComponent(text);

            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.timeout = 5000;
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            var result = '';
                            if (data && data[0]) {
                                for (var i = 0; i < data[0].length; i++) {
                                    if (data[0][i] && data[0][i][0]) {
                                        result += data[0][i][0];
                                    }
                                }
                            }
                            callback(result || text);
                        } catch(e) {
                            callback(text);
                        }
                    } else {
                        callback(text);
                    }
                }
            };
            xhr.ontimeout = function() { callback(text); };
            xhr.onerror   = function() { callback(text); };
            xhr.send();
        } catch(e) {
            callback(text);
        }
    }

    // --- Xu ly hang doi dich ---
    function processQueue() {
        if (isTranslating || pendingQueue.length === 0) return;
        isTranslating = true;

        var item = pendingQueue.shift();
        var text = item.text;

        // Da co trong cache -> dung luon
        if (viDict[text]) {
            item.callback(viDict[text]);
            isTranslating = false;
            setTimeout(processQueue, 0);
            return;
        }

        // Goi Google Translate
        googleTranslate(text, function(translated) {
            if (translated && translated !== text) {
                viDict[text] = translated;
                saveCache();
            }
            item.callback(translated || text);
            isTranslating = false;
            setTimeout(processQueue, BATCH_DELAY);
        });
    }

    // --- Them vao hang doi ---
    function translateAsync(text, callback) {
        if (viDict[text]) {
            callback(viDict[text]);
            return;
        }
        pendingQueue.push({ text: text, callback: callback });
        processQueue();
    }

    // --- Thu nho font cua Label ---
    function scaleDownFont(labelComp) {
        if (!labelComp) return;
        try {
            var fs = labelComp.fontSize || labelComp._fontSize;
            if (fs && fs > MIN_FONT) {
                var newFs = Math.max(MIN_FONT, Math.round(fs * FONT_SCALE));
                if (labelComp.fontSize !== undefined) {
                    labelComp.fontSize = newFs;
                } else {
                    labelComp._fontSize = newFs;
                }
            }
        } catch(e) {}
    }

    // --- Hook cc.Label.string setter ---
    function hookLabel() {
        if (typeof cc === 'undefined' || !cc.Label) return;

        var proto = cc.Label.prototype;

        // Cach 1: Hook qua property descriptor
        var desc = Object.getOwnPropertyDescriptor(proto, 'string');
        if (desc && desc.set) {
            var originalSet = desc.set;
            Object.defineProperty(proto, 'string', {
                get: desc.get,
                set: function(val) {
                    if (isChinese(val)) {
                        var self = this;
                        scaleDownFont(self);
                        // Hien thi tam thoi chu Viet neu da co trong cache
                        if (viDict[val]) {
                            originalSet.call(self, viDict[val]);
                        } else {
                            // Giu nguyen trong khi cho dich
                            originalSet.call(self, val);
                            translateAsync(val, function(vi) {
                                try {
                                    originalSet.call(self, vi);
                                } catch(e) {}
                            });
                        }
                    } else {
                        originalSet.call(this, val);
                    }
                },
                configurable: true
            });
            console.log('[VI HOA] Hook cc.Label.string OK (property)');
            return true;
        }

        // Cach 2: Hook _setString truc tiep
        if (proto._setString) {
            var orig = proto._setString;
            proto._setString = function(val) {
                if (isChinese(val)) {
                    var self = this;
                    scaleDownFont(self);
                    if (viDict[val]) {
                        return orig.call(self, viDict[val]);
                    } else {
                        orig.call(self, val);
                        translateAsync(val, function(vi) {
                            try { orig.call(self, vi); } catch(e) {}
                        });
                        return;
                    }
                }
                return orig.call(this, val);
            };
            console.log('[VI HOA] Hook cc.Label._setString OK');
            return true;
        }

        return false;
    }

    // --- Hook cc.RichText tuong tu ---
    function hookRichText() {
        if (typeof cc === 'undefined' || !cc.RichText) return;
        var proto = cc.RichText.prototype;
        var desc = Object.getOwnPropertyDescriptor(proto, 'string');
        if (desc && desc.set) {
            var originalSet = desc.set;
            Object.defineProperty(proto, 'string', {
                get: desc.get,
                set: function(val) {
                    if (isChinese(val)) {
                        var self = this;
                        if (viDict[val]) {
                            originalSet.call(self, viDict[val]);
                        } else {
                            originalSet.call(self, val);
                            translateAsync(val, function(vi) {
                                try { originalSet.call(self, vi); } catch(e) {}
                            });
                        }
                    } else {
                        originalSet.call(this, val);
                    }
                },
                configurable: true
            });
            console.log('[VI HOA] Hook cc.RichText.string OK');
        }
    }

    // --- Doi cc san sang roi hook ---
    // cc co the chua load ngay khi script chay
    var hookInterval = setInterval(function() {
        if (typeof cc !== 'undefined' && cc.Label) {
            clearInterval(hookInterval);
            var ok = hookLabel();
            hookRichText();
            if (!ok) {
                // Thu lai sau 1s neu hook that bai
                setTimeout(function() {
                    hookLabel();
                    hookRichText();
                }, 1000);
            }
            console.log('[VI HOA] San sang! Cache hien tai: '
                + Object.keys(viDict).length + ' chuoi');
        }
    }, 200);

    // --- Export de debug trong console ---
    window._viHoa = {
        getCache  : function() { return viDict; },
        clearCache: function() {
            viDict = {};
            localStorage.removeItem(CACHE_KEY);
            console.log('[VI HOA] Da xoa cache');
        },
        stats: function() {
            console.log('[VI HOA] Cache: ' + Object.keys(viDict).length + ' chuoi');
            console.log('[VI HOA] Hang doi: ' + pendingQueue.length + ' chuoi cho dich');
        }
    };

    console.log('[VI HOA] Hook da duoc nap!');
})();
// ============================================
// KET THUC VI HOA HOOK
// ============================================
"""

def main():
    if not os.path.exists(INPUT_JS):
        print(f"[LOI] Khong tim thay {INPUT_JS}")
        print("      Dat script nay cung thu muc voi index.js")
        return

    # Kiem tra da inject chua
    with open(INPUT_JS, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'VI HOA HOOK' in content:
        print("[!] index.js da duoc inject hook roi!")
        print("    Neu muon inject lai, xoa phan '// VI HOA HOOK' den cuoi file truoc")
        return

    # Backup
    if not os.path.exists(BACKUP_JS):
        shutil.copy2(INPUT_JS, BACKUP_JS)
        print(f"[1/2] Backup -> {BACKUP_JS}")
    else:
        print(f"[1/2] Backup da co: {BACKUP_JS}")

    # Inject hook vao cuoi file
    new_content = content + HOOK_CODE

    with open(INPUT_JS, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[2/2] Da inject hook vao {INPUT_JS}")
    print()
    print("========== HOAN THANH ==========")
    print("  Hook se lam gi:")
    print("  - Tu dong dich moi text tieng Trung hien thi trong game")
    print("  - Thu nho font 30% (min 12px)")
    print("  - Cache ket qua vao localStorage (offline lan sau)")
    print("  - Can mang cho lan dich dau tien")
    print()
    print("  Debug trong browser console:")
    print("  > _viHoa.stats()      - xem so chuoi da cache")
    print("  > _viHoa.getCache()   - xem noi dung cache")
    print("  > _viHoa.clearCache() - xoa cache de dich lai")
    print()
    print("  Khoi phuc: copy index_before_hook.js -> index.js")
    print("================================")

if __name__ == "__main__":
    main()