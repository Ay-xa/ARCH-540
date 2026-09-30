# 共享计算引擎 `_shared/`

2026-09-30 从 `Version_06/wwr-tool.html` 抽出。**Version_06 的文件没有改动**，它继续用自己文件里的同一份代码；本目录供 `Zoning/` 分支和以后愿意改用共享文件的版本使用。

| 文件 | 内容 | 与 V06 的关系 |
|---|---|---|
| `wwr-climate.js` | `T_HOT`、`CLIM`（三站汇总数据）、`HOURLY`（逐小时数据），另挂 `window.WWR_CLIMATE` | V06 第 330–390 行逐字复制 |
| `wwr-engine.js` | 计算引擎，挂在 `window.WWR` | 见下表 |
| `engine-test.html` | 引擎自检 49 项 + 与 V06 `digest()` 逐字段比对（经 http 打开时在隐藏框架里加载 V06） | 只读 V06 |
| `verify_extract.py` | 证明标注「逐字复制」的函数与 V06 一字不差 | 只读 V06 |

## 引擎里有什么

| 函数 / 常数 | 来源 |
|---|---|
| `DIRS, OVH_LIMIT, OVH_GOOD, ovhScore, MASS, VENT, HOT_TIP, clamp, rad, norm, interpN, dirName` | 逐字复制 |
| `sunPos, sunFor` | 逐字复制 |
| `simulateHours(p, hr, sun)` | **通用化**：`p.groups = [{Ag, hw}, …]` 允许多种尺寸的窗（各组分别算挑檐遮挡）。只有一组时每一步算式与 V06 相同，数值逐位相等 |
| `windowsFromWwr(len, wwr, n, sill, head, H)` | V06 `calc()` 前 6 行：从窗墙比生成 n 扇等大均匀的窗，含 V06 的三处截断（窗头 ≤ 吊顶、最小窗高 0.4、总窗宽 ≤ 墙长 90%） |
| `calcSegment(seg, ctx)` | **通用化的 V06 `calc()`**：输入一段墙 `{len, az, oh, windows:[{w,h,sill}]}` 和上下文 `{H, floors, depth, A, clim, mass, vent}`，不读任何全局。同尺寸的窗归为一组，组内算式同 V06，组间相加。多出 `Wx`（冬季得热 / 房间面积）、`Hx`（= hotPer）、`groups`、`hourly: null`（预留） |
| `calcFacadeFromWwr(k, len, az, fac, ctx)` | V06 等价层：`windowsFromWwr` + `calcSegment`，字段集合与 V06 `calc(k)` 一致 |
| `aggregateBuilding(R, keys, box)` | V06 `calcAll()` 的汇总部分逐字复制 |
| `segmentsForWall(wall, windows)` | 分区分支：窗段与空墙段交替切段 |
| `ZG, kernelCell, sunPatch, gridCells(box), gridConditions(R, box)` | 逐字复制；只把读全局 `S` 改为参数 `box = {L, W, depth, grid}` |
| `COND, ramp, condScore, suitability, suitGrid, stripMean` | 逐字复制（只按配置表循环，不含功能名） |
| `V06_DEFAULT, digestV06()` | V06 默认方案与它的 `digest()`（6 组 × 4 立面），用于比对 |

## 约定

1. 引擎不读、不写任何界面状态；所有输入通过参数传入。
2. 引擎里没有功能名称、房间名称、朝向规则。
3. 墙的方向：绕平面逆时针（南→东→北→西）；每面墙的起点是从室外看的左端；窗的 `u` = 窗左边缘到起点的距离。Rhino 导入时外墙轮廓取逆时针（外法线向外）即与此一致。
4. 单位：米、度、kWh。

## 验证（2026-09-30）

- `verify_extract.py`：气候数据块（313 662 字符）与 23 个函数 / 常数全部逐字相同。
- `engine-test.html`：自检 49 项通过；与 V06 `digest()` 共有的 **1608 个数字逐位相同**（无末位差异）；引擎多出 `oh / Wx / Hx` 三个字段各 24 个。
- V06 `wwr-tool.html` SHA-256 `786656bf954c12cca8a539f6bf444b54adf062cab1286042a62267bf2550384a`。

## 怎么用

```html
<script src="../../_shared/wwr-climate.js"></script>
<script src="../../_shared/wwr-engine.js"></script>
<script>
  const r = WWR.calcSegment({len:20, az:180, oh:0, windows:[{w:2.5,h:1.8,sill:0.6}]},
                            {H:3.0, floors:1, depth:5, A:{...}, clim:'apNow', mass:'mid', vent:'win'});
</script>
```

经 http 打开自检页：`python -m http.server 8766 --directory Passivehouse_Tool/01_Prototypes`，然后访问 `http://localhost:8766/_shared/engine-test.html`。
