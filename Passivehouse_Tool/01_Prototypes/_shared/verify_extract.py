# -*- coding: utf-8 -*-
"""verify_extract.py — 证明共享引擎里标注「逐字复制」的部分与 Version_06/wwr-tool.html 一字不差。

用法（在 01_Prototypes 目录）：python _shared/verify_extract.py
检查：1) wwr-climate.js 的 CLIM:BEGIN…CLIM:END 块与 V06 第 330–390 行逐字相同；
      2) 下列函数 / 常数在两个文件里的文本逐字相同（去掉首尾空白后比较）。
Version_06 的文件只读，不写。
"""
import io, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
V06 = os.path.join(HERE, '..', 'Version_06', 'wwr-tool.html')
CLIMATE = os.path.join(HERE, 'wwr-climate.js')
ENGINE = os.path.join(HERE, 'wwr-engine.js')

def read(p):
    return io.open(p, encoding='utf-8').read()

def func_text(src, name):
    """取 `function name(` 起、到配对的右花括号为止的文本。"""
    m = re.search(r'\bfunction ' + re.escape(name) + r'\(', src)
    if not m:
        return None
    i = m.start(); depth = 0; started = False
    while i < len(src):
        ch = src[i]
        if ch == '{':
            depth += 1; started = True
        elif ch == '}':
            depth -= 1
            if started and depth == 0:
                return src[m.start():i + 1]
        i += 1
    return None

def const_line(src, name):
    m = re.search(r'^\s*const ' + re.escape(name) + r'\b.*$', src, re.M)
    return m.group(0).strip() if m else None

def main():
    v06 = read(V06); clim = read(CLIMATE); eng = read(ENGINE)
    ok = True
    out = []
    # 1 气候数据块
    v_lines = v06.split('\n')
    b = v_lines.index('/* CLIM:BEGIN */'); e = v_lines.index('/* CLIM:END */')
    v_block = '\n'.join(v_lines[b:e + 1])
    c_lines = clim.split('\n')
    cb = c_lines.index('/* CLIM:BEGIN */'); ce = c_lines.index('/* CLIM:END */')
    c_block = '\n'.join(c_lines[cb:ce + 1])
    same = v_block == c_block
    ok &= same
    out.append(('气候数据块 CLIM:BEGIN…END（V06 第 %d–%d 行，%d 字符）' % (b + 1, e + 1, len(v_block)), same))
    # 2 逐字复制的函数
    funcs = ['ovhScore', 'interpN', 'dirName', 'sunPos', 'sunFor', 'kernelCell', 'sunPatch', 'condScore', 'suitability', 'suitGrid', 'stripMean']
    for f in funcs:
        a = func_text(v06, f); bb = func_text(eng, f)
        same = a is not None and bb is not None and a.strip() == bb.strip()
        ok &= same
        out.append(('function ' + f, same))
    consts = ['DIRS', 'OVH_LIMIT', 'MASS', 'VENT', 'HOT_TIP', 'clamp', 'rad', 'norm', 'ZG', 'COND', 'ramp']
    for c in consts:
        a = const_line(v06, c); bb = const_line(eng, c)
        same = a is not None and bb is not None and a == bb
        ok &= same
        out.append(('const ' + c, same))
    # 3 V06 校验值
    h = hashlib.sha256(io.open(V06, 'rb').read()).hexdigest()
    for name, s in out:
        sys.stdout.write(('OK   ' if s else 'DIFF ') + name + '\n')
    sys.stdout.write('Version_06/wwr-tool.html SHA-256 ' + h + '\n')
    sys.stdout.write('ALL IDENTICAL\n' if ok else 'SOME DIFFER\n')
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
