"""
epw_to_clim.py — 从 EPW 气象文件生成窗墙比推敲器所用的气候数组。

用法（在任何目录运行均可）：
    python epw_to_clim.py                 # 写出 ../02_Data/clim.json
    python inject_clim.py <wwr-tool.html> # 把 clim.json 写进工具文件

方法（每个文件相同）：
- 太阳位置：NOAA 简化算法，每小时取小时中点，本地标准时。
- 垂直面辐射 I_vert = DNI·max(0,cosθ) + DHI/2 + GHI·albedo/2，albedo = 0.2（各向同性天空）。
- 24 个朝向：0°(北),15°,…,345°，顺时针。
- GW / GS / GH：采暖季(10–4 月) / 夏季(6–8 月) / 高温时段(室外干球 > T_HOT) 的 I_vert 累计，kWh/m²。
- DW / DS / DH：对应时段直射分量占比。
- PW / PS / PH：对应时段直射加权平均剖面角，度。剖面角 = atan(tan(alt)/cos(az−facAz))。
- Gt：10–4 月、基准 20 °C 的采暖度时数，kKh/a。
- hH：全年室外 > T_HOT 的小时数；h25 / h28：> 25 / 28 °C 小时数。
"""
import math, json, os, sys, datetime
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding='utf-8')  # Windows 终端中文输出

T_HOT = 22.0          # 高温时段阈值，°C（取值理由见 PLAN_v02.md §5）
N_DIR = 24            # 朝向数
ALBEDO = 0.2
HEATING_MONTHS = (10, 11, 12, 1, 2, 3, 4)
SUMMER_MONTHS = (6, 7, 8)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', '02_Data')

FILES = [
    ('apNow', 'CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw', '当下（机场站）',
     'CWEC2020 典型年，温哥华国际机场站（Climate.OneBuilding.org）。与 2080 年文件同源，两者的差异只反映气候变化'),
    ('hbNow', 'CAN_BC_Vancouver.Harbour.CS.712010_TMYx.2009-2023.epw', '当下（港口站）',
     'TMYx 2009–2023 典型年，温哥华港 Harbour CS 站（Climate.OneBuilding.org）。适合市中心场地；与机场站的差异混有站点和数据集方法的差异'),
    ('f2080', 'MORPHED_SSP585_2080s_CAN_BC_VANCOUVER-INTL-A_CWEC2020.epw', '2080 年预测',
     'CWEC2020 机场站按 SSP5-8.5 情景移位到 2080 年代（PCIC）。只有气温、湿度、气压被移位，太阳辐射与机场站当下完全相同'),
]


def solar_position(lat, lon, tz, doy, hour_local):
    """返回 (高度角°, 方位角° 自北顺时针)。NOAA 简化公式。"""
    g = 2 * math.pi / 365 * (doy - 1 + (hour_local - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour_local * 60 + eqt + 4 * lon - 60 * tz
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    sa = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    alt = math.asin(max(-1, min(1, sa)))
    x = -math.sin(ha) * math.cos(decl)
    y = math.sin(decl) * math.cos(la) - math.cos(decl) * math.sin(la) * math.cos(ha)
    az = math.degrees(math.atan2(x, y)) % 360
    return math.degrees(alt), az


def vertical_irradiance(alt, az, fac_az, dni, dhi, ghi, albedo=ALBEDO):
    """返回 (直射分量, 总量) W/m²，垂直面朝向 fac_az。"""
    c = math.cos(math.radians(alt)) * math.cos(math.radians(az - fac_az))
    beam = dni * c if c > 0 else 0.0
    diffuse = dhi * 0.5 + ghi * albedo * 0.5
    return beam, beam + diffuse


def profile_angle(alt, az, fac_az):
    """太阳剖面角（投影到立面法线竖直面上的高度角），度；太阳在立面背后时返回 None。"""
    c = math.cos(math.radians(az - fac_az))
    if c <= 0:
        return None
    return math.degrees(math.atan(math.tan(math.radians(alt)) / c))


def read_epw(path):
    lines = open(path, encoding='latin-1').read().splitlines()
    loc = lines[0].split(',')
    meta = dict(station=loc[1].strip(), lat=float(loc[6]), lon=float(loc[7]), tz=float(loc[8]))
    rows = []
    doy, last = 0, None
    for l in lines[8:]:
        if not l.strip():
            continue
        r = l.split(',')
        m, d, h = int(r[1]), int(r[2]), int(r[3])
        if (m, d) != last:
            doy += 1
            last = (m, d)

        def num(i):
            v = float(r[i])
            return 0.0 if v >= 9999 else v
        rows.append(dict(month=m, day=d, hour=h, doy=doy, T=float(r[6]), ghi=num(13), dni=num(14), dhi=num(15)))
    return meta, rows


def process_rows(rows, lat, lon, tz, t_hot=T_HOT, n_dir=N_DIR):
    """核心累加。rows 为 read_epw 输出；返回数组字典。"""
    fac = [i * 360 / n_dir for i in range(n_dir)]
    acc = {s: dict(beam=[0.0] * n_dir, tot=[0.0] * n_dir, pw=[0.0] * n_dir) for s in 'WSH'}
    Gt = 0.0
    T = []; summerT = []; h25 = h28 = hH = 0
    for r in rows:
        t = r['T']; m = r['month']
        T.append(t)
        if m in SUMMER_MONTHS:
            summerT.append(t)
        if m in HEATING_MONTHS:
            Gt += max(0.0, 20.0 - t)
        if t > 25: h25 += 1
        if t > 28: h28 += 1
        hot = t > t_hot
        if hot: hH += 1
        if r['ghi'] <= 0 and r['dni'] <= 0:
            continue
        alt, az = solar_position(lat, lon, tz, r['doy'], r['hour'] - 0.5)
        if alt <= 0:
            continue
        seasons = []
        if m in HEATING_MONTHS: seasons.append('W')
        if m in SUMMER_MONTHS: seasons.append('S')
        if hot: seasons.append('H')
        if not seasons:
            continue
        for i, fa in enumerate(fac):
            beam, tot = vertical_irradiance(alt, az, fa, r['dni'], r['dhi'], r['ghi'])
            pa = profile_angle(alt, az, fa) if beam > 0 else None
            for s in seasons:
                a = acc[s]
                a['beam'][i] += beam
                a['tot'][i] += tot
                if pa is not None:
                    a['pw'][i] += beam * pa
    out = {}
    for s in 'WSH':
        b, tt, pw = acc[s]['beam'], acc[s]['tot'], acc[s]['pw']
        out['G' + s] = [round(x / 1000) for x in tt]
        out['D' + s] = [round(b[i] / tt[i], 2) if tt[i] else 0 for i in range(n_dir)]
        out['P' + s] = [round(pw[i] / b[i]) if b[i] else 0 for i in range(n_dir)]
    out['Gt'] = round(Gt / 1000, 1)
    out['Tmean'] = round(sum(T) / len(T), 1) if T else 0
    out['Tmax'] = round(max(T), 1) if T else 0
    out['Tsummer'] = round(sum(summerT) / len(summerT), 1) if summerT else 0
    out['h25'] = h25; out['h28'] = h28; out['hH'] = hH
    return out


def main():
    result = dict(meta=dict(generated=datetime.date.today().isoformat(), T_HOT=T_HOT, n_dir=N_DIR, albedo=ALBEDO,
                            heating_months=list(HEATING_MONTHS), summer_months=list(SUMMER_MONTHS),
                            script='03_Scripts/epw_to_clim.py'), sets={})
    for key, fname, label, note in FILES:
        path = os.path.join(DATA, 'EPW', fname)
        meta, rows = read_epw(path)
        out = process_rows(rows, meta['lat'], meta['lon'], meta['tz'])
        out.update(label=label, note=note, station=meta['station'], lat=meta['lat'], lon=meta['lon'], file=fname)
        result['sets'][key] = out
        print(f"{key:6s} {meta['station']:22s} Gt {out['Gt']:5.1f}  hH(>{T_HOT:g}) {out['hH']:5d}  h25 {out['h25']:4d}  "
              f"GW[S] {out['GW'][12]}  GS[S] {out['GS'][12]}  GH[S] {out['GH'][12]}  GH[W] {out['GH'][18]}", file=sys.stderr)
    outpath = os.path.join(DATA, 'clim.json')
    json.dump(result, open(outpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('written', os.path.relpath(outpath), file=sys.stderr)


if __name__ == '__main__':
    main()
