"""
inject_clim.py — 把 02_Data/clim.json 写进工具 HTML 的 /* CLIM:BEGIN */ … /* CLIM:END */ 区间。

用法：python inject_clim.py ../01_Prototypes/Version_02/wwr-tool.html
"""
import json, os, re, sys
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
CLIM_JSON = os.path.join(HERE, '..', '02_Data', 'clim.json')
BEGIN, END = '/* CLIM:BEGIN */', '/* CLIM:END */'


def js_array(a):
    return '[' + ','.join(str(x) for x in a) + ']'


def js_set(key, d):
    lines = [f"  {key}:{{label:{json.dumps(d['label'], ensure_ascii=False)},note:{json.dumps(d['note'], ensure_ascii=False)},",
             f"    station:{json.dumps(d['station'])},file:{json.dumps(d['file'])},lat:{d['lat']},lon:{d['lon']},",
             f"    Gt:{d['Gt']},Tmean:{d['Tmean']},Tsummer:{d['Tsummer']},Tmax:{d['Tmax']},h25:{d['h25']},h28:{d['h28']},hH:{d['hH']},"]
    for k in ('GW', 'GS', 'GH', 'DW', 'DS', 'DH', 'PW', 'PS', 'PH'):
        lines.append(f"    {k}:{js_array(d[k])},")
    lines[-1] = lines[-1].rstrip(',') + '}'
    return '\n'.join(lines)


def build_block(data):
    m = data['meta']
    order = [k for k in ('apNow', 'hbNow', 'f2080') if k in data['sets']] + [k for k in data['sets'] if k not in ('apNow', 'hbNow', 'f2080')]
    sets = ',\n'.join(js_set(k, data['sets'][k]) for k in order)
    return (f"{BEGIN}\n"
            f"// 由 03_Scripts/inject_clim.py 从 02_Data/clim.json 生成（{m['generated']}），请勿手改；改数据请重跑 epw_to_clim.py。\n"
            f"// 每个数组 {m['n_dir']} 项 = 立面方位角 0°,15°,…,345°（0=北，90=东，180=南，270=西）。\n"
            f"// GW/GS/GH：采暖季(10–4 月)/夏季(6–8 月)/高温时段(室外 > T_HOT) 垂直面辐射累计 kWh/m²（各向同性天空，地面反射率 {m['albedo']}）。\n"
            f"// DW/DS/DH：其中直射占比。PW/PS/PH：直射加权平均剖面角，度。Gt：10–4 月、基准 20 °C 采暖度时数 kKh/a。\n"
            f"// hH：全年室外 > T_HOT 小时数；h25/h28：> 25/28 °C 小时数。\n"
            f"const T_HOT={m['T_HOT']:g};\n"
            f"const CLIM={{\n{sets}\n}};\n"
            f"{END}")


def main():
    if len(sys.argv) < 2:
        sys.exit('用法：python inject_clim.py <wwr-tool.html>')
    html_path = sys.argv[1]
    data = json.load(open(CLIM_JSON, encoding='utf-8'))
    html = open(html_path, encoding='utf-8').read()
    if BEGIN not in html or END not in html:
        sys.exit(f'{html_path} 中找不到 {BEGIN} / {END} 标记')
    pattern = re.compile(re.escape(BEGIN) + r'.*?' + re.escape(END), re.S)
    new_html, n = pattern.subn(lambda _: build_block(data), html, count=1)
    open(html_path, 'w', encoding='utf-8').write(new_html)
    print(f'已写入 {os.path.relpath(html_path)}：{len(data["sets"])} 组气候数据，T_HOT={data["meta"]["T_HOT"]:g} °C')


if __name__ == '__main__':
    main()
