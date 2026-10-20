import sys, math
epw, out = sys.argv[1], sys.argv[2]
rows = open(epw, encoding='utf-8', errors='replace').read().splitlines()
loc = rows[0].split(',')
data = [r.split(',') for r in rows[8:] if r.strip()]
assert len(data) == 8760, len(data)
ghi = [int(float(r[13])) for r in data]
dni = [int(float(r[14])) for r in data]
dhi = [int(float(r[15])) for r in data]
mo = [int(r[1]) for r in data]; dy = [int(r[2]) for r in data]; hr = [int(r[3]) for r in data]
assert mo[0] == 1 and dy[0] == 1 and hr[0] == 1 and mo[-1] == 12 and dy[-1] == 31 and hr[-1] == 24
js = ('// 温哥华国际机场 CWEC2020 逐小时太阳辐射（Wh/m²，每个数是这一小时之前一小时的累计；EPW 第 14、15 列）\n'
      '// 来源：Passivehouse_Tool/02_Data/EPW/CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw（Climate.OneBuilding.Org，Environment Canada CWEC2020），2026-10-19 用 epw_to_js.py 转换\n'
      'const WEATHER = { name:"Vancouver Intl AP · CWEC2020", lat:%s, lon:%s, tz:%s,\n'
      '  dni:"%s",\n  dhi:"%s" };\n') % (loc[6], loc[7], loc[8], ','.join(map(str, dni)), ','.join(map(str, dhi)))
open(out, 'w', encoding='utf-8', newline='\n').write(js)
print('bytes', len(js.encode('utf-8')))
print('annual GHI kWh/m2', round(sum(ghi) / 1000, 1), 'DNI', round(sum(dni) / 1000, 1), 'DHI', round(sum(dhi) / 1000, 1))
