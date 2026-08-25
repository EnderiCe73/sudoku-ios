"""
subset_font.py
将思源黑体子集化到约 2MB,仅保留:
  - 全部 ASCII 可打印字符
  - 常见中文标点(全角)
  - GB2312 一级常用汉字(3755 个,覆盖 99%+ 日常中文)
  - 应用源码中出现的所有字符
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SRC_FONT = ROOT / "chinese.full.ttf"    # 始终从完整备份读取(避免读写冲突)
OUT_FONT = ROOT / "chinese.ttf"          # 输出到实际使用路径
BACKUP_FONT = ROOT / "chinese.full.ttf"  # 完整字体备份(作为源)
CHARS_FILE = ROOT / "subset_chars.txt"
TEMP_OUT = ROOT / "chinese.tmp.ttf"      # 临时输出,成功后替换


def build_charset():
    chars = set()

    # 1. ASCII 可打印字符 (0x20 ~ 0x7E)
    for cp in range(0x20, 0x7F):
        chars.add(chr(cp))

    # 2. 常见中文标点(全角)
    punct = "，。！？：；、""''（）【】《》—…·「」『』"
    chars.update(punct)

    # 3. 全角数字与字母(防止意外使用)
    for cp in range(0xFF10, 0xFF1A):   # ０-９
        chars.add(chr(cp))
    for cp in range(0xFF21, 0xFF3B):   # Ａ-Ｚ
        chars.add(chr(cp))
    for cp in range(0xFF41, 0xFF5B):   # ａ-ｚ
        chars.add(chr(cp))

    # 4. GB2312 一级常用汉字 (3755 个)
    # GB2312 一级汉字编码范围:0xB0A1 ~ 0xF7FE
    # 区位码:16-55 区,每区 94 个汉字
    for qu in range(16, 56):                 # 16 ~ 55 区
        for wei in range(1, 95):             # 01 ~ 94 位
            high = 0xA0 + qu
            low = 0xA0 + wei
            try:
                ch = bytes([high, low]).decode("gb2312")
                chars.add(ch)
            except (UnicodeDecodeError, KeyError):
                pass

    # 5. 扫描应用源码,把出现的所有字符加入
    for py_file in [ROOT / "main.py", ROOT / "sudoku_core.py"]:
        if py_file.exists():
            text = py_file.read_text(encoding="utf-8")
            chars.update(text)

    return chars


def main():
    # 1. 确保完整备份存在(从未子集化过的情况)
    current_font = ROOT / "chinese.ttf"
    if not BACKUP_FONT.exists():
        if not current_font.exists():
            print(f"[ERROR] 未找到字体文件: {current_font}")
            sys.exit(1)
        import shutil
        shutil.copy2(current_font, BACKUP_FONT)
        print(f"[OK] 已备份原始字体到: {BACKUP_FONT.name} ({BACKUP_FONT.stat().st_size/1024/1024:.1f} MB)")
    else:
        print(f"[OK] 完整字体备份存在: {BACKUP_FONT.name} ({BACKUP_FONT.stat().st_size/1024/1024:.1f} MB)")

    # 2. 构建字符集
    chars = build_charset()
    print(f"[OK] 字符集大小: {len(chars)} 个字符")

    # 3. 写入字符文件
    CHARS_FILE.write_text("".join(sorted(chars)), encoding="utf-8")
    print(f"[OK] 字符列表已写入: {CHARS_FILE.name}")

    # 4. 调用 pyftsubset 子集化(输入完整备份,输出到临时文件)
    # 关键参数说明:
    #   --no-hinting            移除 hinting 指令(CJK 字体上可省 40%+ 体积,iOS 高分屏不需要)
    #   --layout-features-='*' 移除所有 GSUB/GPOS 排版特性(本应用纯文本显示不需要)
    #   --ignore-missing-unicodes  跳过字体里没有的字符
    #   --recalc-bounds         重新计算字体的 bounding box
    #   --desubroutinize        展开 CFF 子程序(若用 OTF 轮廓)
    #   --drop-tables+=kern,vhea,vmtx,fpgm,prep,cvt  显式丢弃不需要的表
    cmd = [
        sys.executable, "-m", "fontTools.subset",
        str(BACKUP_FONT),
        "--text-file=" + str(CHARS_FILE),
        "--output-file=" + str(TEMP_OUT),
        "--no-hinting",
        "--layout-features-=*",
        "--ignore-missing-unicodes",
        "--recalc-bounds",
        "--recalc-timestamp",
        "--desubroutinize",
        "--drop-tables+=kern,vhea,vmtx,fpgm,prep,cvt,GSUB,GPOS",
    ]
    print("[INFO] 正在子集化,请稍候...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERROR] pyftsubset 失败:")
        print(result.stderr)
        if result.stdout:
            print("--- stdout ---")
            print(result.stdout)
        sys.exit(1)

    # 5. 成功后替换 chinese.ttf
    import shutil
    if TEMP_OUT.exists():
        shutil.move(str(TEMP_OUT), str(OUT_FONT))
    else:
        print(f"[ERROR] 临时输出文件未生成: {TEMP_OUT}")
        sys.exit(1)

    # 6. 输出结果统计
    src_size = BACKUP_FONT.stat().st_size / 1024 / 1024
    out_size = OUT_FONT.stat().st_size / 1024 / 1024
    ratio = out_size / src_size * 100

    print("")
    print("=" * 50)
    print(f"原始字体:   {src_size:.2f} MB ({BACKUP_FONT.name})")
    print(f"子集字体:   {out_size:.2f} MB ({OUT_FONT.name})")
    print(f"压缩比:    保留 {ratio:.1f}% 体积")
    print("=" * 50)

    if out_size > 3.0:
        print(f"[WARN] 体积仍偏大 ({out_size:.2f} MB > 3 MB)")
        print("       可改为只保留应用源码字符(注释掉 build_charset 中的 GB2312 部分)")
    elif out_size < 0.3:
        print(f"[INFO] 体积已很小 ({out_size:.2f} MB),仅含应用必需字符")
    else:
        print(f"[OK] 体积处于合理范围 ({out_size:.2f} MB ≈ 2MB 目标)")


if __name__ == "__main__":
    main()
