"""把 EPW 气象文件里的逐小时风向、风速转成工具用的数据（2026-10-19）。

用法：python epw_wind_to_js.py 输入.epw
输出：一行 JavaScript（const WIND_RAW = {...};），贴进 Version_01/index.html。

只取 EPW 的第 21 列（风向，度，从正北顺时针，指风吹来的方向）和第 22 列（风速，m/s），8,760 小时，
风向取整到 1°，风速保留 1 位小数。第 i 个值 = 一年里第 i 个小时（第 i // 24 天，i % 24 点到 i % 24 + 1 点）。
统计（风玫瑰、立面迎风、按日期范围和使用时段筛选）都在工具里算。
"""
import csv
import json
import sys


def main(path):
    with open(path, encoding="latin-1") as f:
        rows = list(csv.reader(f))
    data = rows[8:]
    assert len(data) == 8760, len(data)
    dirs = ",".join(str(int(round(float(r[20])))) for r in data)
    spds = ",".join(("%.1f" % float(r[21])).rstrip("0").rstrip(".") for r in data)
    out = {"name": "Vancouver Intl AP · CWEC2020", "dir": dirs, "spd": spds}
    print("const WIND_RAW = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
