"""手算核对用例。运行：python test_epw_to_clim.py"""
import sys, os
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding='utf-8')  # Windows 终端中文输出
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epw_to_clim import solar_position, vertical_irradiance, profile_angle, process_rows

LAT, LON, TZ = 49.19, -123.18, -8.0
fails = 0


def check(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got:.2f}, want {want:.2f} ±{tol}")


# 1. 太阳位置：夏至(第172天)、冬至(第355天)正午最高高度角 = 90 − 纬度 ± 23.44
for doy, want, nm in ((172, 90 - LAT + 23.44, '夏至'), (355, 90 - LAT - 23.44, '冬至')):
    best = max(((solar_position(LAT, LON, TZ, doy, h / 60)[0], h / 60) for h in range(10 * 60, 15 * 60)), key=lambda x: x[0])
    check(f'{nm}正午高度角', best[0], want, 0.5)
    check(f'{nm}正午方位角', solar_position(LAT, LON, TZ, doy, best[1])[1], 180, 2.0)

# 2. 垂直面辐射手算：高度角30°、方位180°、DNI 800、DHI 100、GHI 500
#    南向：直射 800·cos30 = 692.8，散射 100/2 + 500·0.2/2 = 100 → 792.8；北向、东向只有散射 100
b, t = vertical_irradiance(30, 180, 180, 800, 100, 500); check('南向直射', b, 692.82, 0.1); check('南向总量', t, 792.82, 0.1)
b, t = vertical_irradiance(30, 180, 0, 800, 100, 500);   check('北向总量', t, 100.0, 0.01)
b, t = vertical_irradiance(30, 180, 90, 800, 100, 500);  check('东向总量', t, 100.0, 0.01)

# 3. 剖面角：正对时等于高度角；偏 45° 时 atan(tan30/cos45) = 39.23°
check('剖面角正对', profile_angle(30, 180, 180), 30.0, 0.01)
check('剖面角偏45°', profile_angle(30, 180, 225), 39.23, 0.05)

# 4. 高温过滤：三行人造数据，同一辐射，气温 21 / 23 / 25 °C，阈值 22 → 只累加后两行
#    用 6 月 21 日 12 时（小时中点 11.5），先算这一刻的南向垂直辐射作为参考
alt, az = solar_position(LAT, LON, TZ, 172, 11.5)
_, ref = vertical_irradiance(alt, az, 180, 800, 100, 500)
rows = [dict(month=6, day=21, hour=12, doy=172, T=T, ghi=500, dni=800, dhi=100) for T in (21, 23, 25)]
out = process_rows(rows, LAT, LON, TZ, t_hot=22)
check('高温小时数', out['hH'], 2, 0)
check('高温时段南向 GH(kWh)', out['GH'][12], round(2 * ref / 1000), 0)   # 两小时累加后四舍五入
check('夏季南向 GS(kWh)', out['GS'][12], round(3 * ref / 1000), 0)       # 三小时都在 6 月
check('>25°C 小时数', out['h25'], 0, 0)                                  # 25 不算 >25
check('采暖度时数(6月不计)', out['Gt'], 0, 0)

print('\n' + ('ALL PASS' if not fails else f'{fails} FAILED'))
sys.exit(1 if fails else 0)
