# ARCH 540 — Work Log

Records are appended after each session. Most recent entry is at the bottom.

---

## 2026-09-18

**Completed**
- Created `Unprotected_Opening_Tool/01_Prototypes/Version_04/index.html` based on V01
- Added Building Position sliders (Offset X / Offset Y, −1 to +1, mapped to full allowed range)
- Added orange ⚠ warning note in sidebar: BCBC table data not independently verified
- Replaced the oblique-projected 3D box in plan view with a proper **architectural isometric / axonometric view** (30°/60°, viewer from SE-above)
  - Parcel renders as flat ground parallelogram
  - Building renders as proper 3D box (roof + East face + South face visible)
  - LD annotation lines drawn on the ground plane from each facade midpoint to property line
  - Drag interaction updated with inverse isometric projection math so dragging follows the correct oblique direction (not the old orthographic formula)

**Key decisions**
- Isometric constants: `AXI = cos(π/6) ≈ 0.866`, `AYI = sin(π/6) = 0.5`; scale `isoSc` computed each render to fit parcel + building height in 800×560 viewBox
- Painter's algorithm order: North → West → East → South → Roof
- LD lines drawn on ground plane (z=0), not floating in 3D — cleaner and easier to read
- All elevations, BCBC calculations, sidebar inputs untouched

**Current state**
- V04 renders and runs without errors
- All four elevation cards (N/S/E/W) display correctly with PASS/FAIL badges
- Drag interaction works with correct isometric direction mapping
- V01, V02, V03 untouched in their folders

**Unresolved**
- ⚠ **BCBC 2024 table data in V01/V04 is UNVERIFIED** — carried from V01, never checked against the actual BCBC 2024 PDF. Must verify before any academic or submission use.
- Table C values are approximate (≈ Table B × 0.68) — source unclear
- LD annotation labels can overlap building geometry when building is near parcel edge — not a blocker but could be improved

**Next session: suggested starting point**
- Open `Unprotected_Opening_Tool/01_Prototypes/Version_04/index.html` in browser to review
- Decide whether to verify BCBC data (check Tables 3.2.3.1-B/C/D/E in BCBC 2024 PDF)
- Or continue with the next visual/UX improvement — possible candidates:
  - Add grid lines to the isometric ground plane
  - Show neighbour building outlines beyond the property line
  - Improve LD label placement in isometric view

---

## 2026-09-18 (session 2)

**Completed**
- Set up folder structure: `Unprotected_Opening_Tool/` with `01_Prototypes/`, `02_Current/`, `03_References/`, `04_Archive/`; `Version_01`/`Version_02` subfolders under `01_Prototypes` (user later added `Version_03` and `Map/` alongside these)
- Reviewed and compared the three opening-tool prototypes (V01 index.html, V02 facade_axo.html, V03 facade_checker.html) in plain language: functionality, tech stack (all vanilla HTML/CSS/JS, no framework), unique features, calculation-logic differences, reusable parts, and known issues/risks. Read-only — no files changed during this review.
- Opened and tested `Unprotected_Opening_Tool/01_Prototypes/Map/Version_01/bcbc_map_v2.html` (Vancouver parcel + zoning lookup via Leaflet + ArcGIS Open Data endpoints). Confirmed click-to-query works (tested on 3129 E 29th Ave → R1-1 zoning, 765 m², 10×33 m).
- Fixed "API KEY REQUIRED" basemap watermark in `Map/Version_01/bcbc_map_v2.html`: swapped the CARTO tile layer (now requires a key) for the free OpenStreetMap standard tile layer. Parcel/zoning query logic untouched.
- Created `Unprotected_Opening_Tool/01_Prototypes/Map/Version_02/bcbc_map_v2.html`: added a Leaflet layer-switcher control positioned under the zoom buttons (top-left), toggling between OpenStreetMap (default, no key needed) and the original CARTO layer (needs key, kept for future use). Verified both layers render and switch correctly; parcel/zoning click lookup still works in both.

**Key decisions**
- New map layer-switcher was built as a separate `Map/Version_02` rather than editing `Map/Version_01` further in place, so V01 stays as the minimal single-basemap reference.
- OpenStreetMap's standard tile server chosen as the default base layer since it needs no API key; CARTO kept as a selectable option in case an API key is obtained later.

**Current state**
- Opening-tool prototypes V01/V02/V03/V04 all untouched by this session except V04 pre-existed from session 1 above — no direction chosen yet, no integration started.
- `Map/Version_01` — basemap fixed, otherwise unchanged.
- `Map/Version_02` — new, adds layer switcher only; parcel/zoning logic identical to V01.

**Unresolved**
- The map tool's "Copy Params for V04" button is intended to feed `01_Prototypes/Version_04/index.html` — that file exists (see session 1 above) but the copy/paste hand-off between the two tools has not actually been tested end-to-end.
- No decision yet on which opening-tool prototype (or combination) to move forward with.
- CARTO layer still needs an API key if it's ever wanted as the default — currently just kept as a secondary, non-functional-without-key option in V02.

**Next session: suggested starting point**
- Decide on next direction for the opening-tool prototypes (verify BCBC data, or pick a prototype to build on)
- If continuing the map tool: test the actual "Copy Params for V04" → paste-into-V04 workflow end-to-end

---

## 2026-09-18 (session 3)

**Completed**
- Opened and reviewed `Map/Version_03/bcbc_map_v3.html` — adds local GeoJSON zoning overlay, point-in-polygon lookup, colour-coded districts, oriented bounding box, and loading overlay. File structure: HTML + separate `vancouver_zoning_wgs84.geojson` (2.5 MB).
- Diagnosed why V03 failed from `file://`: browser blocks `fetch()` calls to local files (CORS restriction).
- Created `Map/Version_04/bcbc_map_v4.html`: embedded the 2.5 MB GeoJSON directly into the HTML as an inline JavaScript variable. No `fetch()`, no server needed — double-click to open.
- Fixed basemap tile issue: OSM blocked requests from `file://` (usage policy) → CartoDB also now requires API key → switched to **Esri World Street Map** (`server.arcgisonline.com`), which is public, no key required, and consistent with the ArcGIS parcel API already used in the tool.
- Confirmed V4 works: 1621 zoning districts loaded, parcel click returns address / zoning / dimensions correctly.

**Key decisions**
- Esri tile layer chosen as the permanent basemap for V4 — no key, works from file://, same data source as the parcel query.
- GeoJSON embedding strategy chosen over local server: simpler workflow, no terminal commands needed before each session.
- V03 kept as reference for the "separate file + server" approach.

**Current state**
- `Map/Version_04/bcbc_map_v4.html` — fully self-contained, double-click to open, all features working ✓
- Map series: V01 (OSM fix) → V02 (layer switcher) → V03 (local GeoJSON, needs server) → V04 (embedded GeoJSON, standalone) ✓
- Opening-tool prototypes (V01–V04) untouched this session.

**Unresolved**
- "Copy Params for V04" → paste-into-opening-tool workflow still untested end-to-end.
- No decision yet on next direction for the opening-tool prototypes.
- ⚠ BCBC table data in opening-tool V04 still unverified against BCBC 2024 PDF.

**Next session: suggested starting point**
- Test "Copy Params for V04" button in Map V4, paste result into opening-tool V4 sliders — confirm the hand-off works
- Or: decide on next development direction (BCBC data verification, or next visual feature for opening-tool V4)

---

## 2026-09-18 (session 4)

**Completed**
- Created `Unprotected_Opening_Tool/01_Prototypes/Version_05/index.html` — a single self-contained HTML file merging Map V4 and Parcel Checker V4 into a two-tab layout.
- Tab 1 (Map): full Leaflet map with embedded GeoJSON zoning overlay and Esri basemap; parcel click loads address, zoning, and bounding-box dimensions in the side panel.
- Tab 2 (Parcel Checker): full BCBC compliance checker with isometric axonometric view, four elevation cards, all sliders.
- Bridge behaviour: selecting a parcel on the map auto-imports Parcel Width E-W and Depth N-S into Tab 2's sliders and switches to Tab 2 automatically. A green banner confirms the import (address + dimensions).
- "← Back to Map" button at the top of Tab 2's sidebar returns to the map; Leaflet `invalidateSize()` fires on return so tiles stay correct.
- Committed as `770c223`.

**Key decisions**
- Parcel Width/Depth are the only values auto-imported from the map; building size, height, occupancy, and neighbour setbacks remain manual in Tab 2.
- `importToChecker()` is injected directly after `showResult()` in the map's click handler, using `lastData.bbox` (already set by showResult) — no changes to showResult itself.
- File size ≈ 2.55 MB (GeoJSON embedded). Open by double-clicking in Chrome/Edge — in-app browser cannot handle files this large.
- "Parcel Checker" tool files are in `01_Prototypes/Parcel Checker/Version_04/` (not `Version_04/` directly as noted in earlier sessions).

**Current state**
- `Version_05/index.html` — fully functional two-tab merged tool ✓
- Map series: V01 → V02 → V03 → V04 (standalone) → V05 (merged with Checker)
- Parcel Checker series: V01 → V02 → V03 → V04 (isometric) → V05 (embedded in merged tool)

**Unresolved**
- ⚠ BCBC table data still unverified against BCBC 2024 PDF — all values carried from V01.
- The "Copy to Clipboard" button in the map panel is now secondary to auto-import but still present.
- No mobile layout tested (file is desktop-first).

**Next session: suggested starting point**
- Open `Version_05/index.html` in Chrome, click a parcel, confirm auto-jump and slider fill work end-to-end.
- Decide whether to verify BCBC table data (check Tables 3.2.3.1-B/C/D/E in BCBC 2024 PDF).


---

## 2026-09-24（含 09-23 深夜；被动房工具）

**Completed**
- 定位 `Passivehouse_Tool/01_Prototypes/Version_01/wwr-tool.html`（窗墙比推敲器），把手写的温哥华气候估算值替换为 EPW 逐小时累加结果，加「当下 / 2080」切换；提交并推送（f2f1aa6）。
- 复制为 `Version_02`，写修改计划 `Version_02/PLAN_v02.md`，经用户确认后分两阶段实施：
  - 第一阶段：下载并核对机场站 CWEC2020（LOCATION 与 2080 文件一致，三列辐射 8760 小时完全相同）；气候选项改为三个（机场站当下 = 默认、港口站当下、2080 年）；过热指标改为「高温时段得热」（室外 > 22 °C 小时的透入辐射）；修复气候按钮焦点丢失、采暖度时数被静默覆盖、基准未记录气候三个前端问题。
  - 第二阶段：每个立面房间逐小时单节点热平衡模拟全年室内温度，输出室内 > 25 °C 小时占比，对照被动房判据（≤10%，建议 ≤5%）；新增热质量（轻/中/重）和开窗通风（不开窗/开窗/穿堂风）预设；「计算假设」新增内部得热、卫生换气、热回收效率。
- 建立可复现的数据管线：`02_Data/EPW/`（三个 EPW + README 记录来源与核对）、`02_Data/clim.json`、`03_Scripts/epw_to_clim.py`（生成）、`inject_clim.py`（写入 HTML 标记区间）、`test_epw_to_clim.py`（15 项手算测试）；页面 `?test=1` 自检 16 项。
- 全部提交并推送到 GitHub（最新 b727ed9）。Version_01 未改动。

**Key decisions**
- 高温阈值 22 °C（非 24）：当下样本量更大，2080 对比仍明显。第一阶段评分锚点 4/20 kWh/m² 为过渡刻度，已被第二阶段替换。
- 机场站 CWEC2020（非 v2）作默认「当下」，因 2080 文件由它移位而来；界面明确只有机场站与 2080 之间的差异才纯粹是气候变化。
- 手改采暖度时数后切换气候保留手动值并显示「恢复」；跨气候设基准允许但标注。
- 数值来源分层：过热判据 10%/5% 与内部得热 2.1 W/m² 已在公开资料核对；热质量 30/50/75 Wh/(m²K)、开窗 2/4 次/h、卫生换气 0.3、热回收 0.75、屋面 U 按外墙 = 估计值，界面与代码注释均标明。
- EPW 源文件从 Google Drive 复制进项目（约 4.8 MB），保证任何电脑可复现。

**Current state**
- `Version_02/wwr-tool.html`（363 KB，内嵌三组逐小时数据）可双击打开；默认方案在机场站当下南立面过热频率 10.3%（刚超判据），2080 年 31.7%。
- `Version_01/wwr-tool.html` 保留为「季节总量 + 两气候」版本。
- 一次完整渲染约 11 ms。

**Unresolved**
- 热质量三档、开窗换气次数等为估计值，若要用于正式汇报需对照 PHPP 手册 / ISO 13790 核实。
- 模型局限：单节点不分空气与表面温度；房间只有一个外立面；无活动遮阳；地面传热忽略。
- 港口站 TMYx 与机场站 CWEC2020 差异混有站点与数据集方法差异，不能当作气候变化解读。
- 场地遮挡角仍是统一 15°，尚未与地块地图工具（Version_05）联动。

**Next session: suggested starting point**
- 在 Chrome 双击打开 `Version_02/wwr-tool.html`，切换三组气候和两组预设，检查设计提示是否符合直觉。
- 候选方向：把过热频率画成逐月 / 逐时热力图；把地块地图的邻近建筑高度接进遮挡角；或对照 PHPP 手册核实热质量档位。

---

## 2026-09-24（session 2；被动房工具室内自动分区）

**Completed**
- 写修改计划 `Version_03/PLAN_zoning.md`（现状、网格采光模型、得热分配、配置表、适合度、分配算法、界面、验收、14 项决定），用户全部按推荐确认。
- 复制 V02 为 `Version_03`，分两阶段实施并各自提交，每阶段由用户在 Chrome 验证：
  - 阶段 A：楼层平面条件网格（默认 1 m）。采光按离窗距离指数衰减（衰减长度 = 窗头高），归一化后房间带平均恰等于立面采光系数；冬季得热 / 夏季过热按直射落点 + 散射衰减 + 一半空气混合分布；三个热力图层随朝向旋转。朝向滑块步长改 1°。自检 34 项。
  - 阶段 B：独立配置表 `zoning-config.js`（公寓：客厅 / 卧室 / 服务区），适合度 = 平滑斜坡评分加权平均，分配 = 空间平滑 + 面积水位法 + Potts/ICM 连片 + 小块清理。分区图层、点格子看分数与解释句。自检 42 项；40°→50° 逐度扫描最大翻转 1.67%。
- 按用户要求 V03 定格为 A + B，复制为 `Version_04` 做阶段 C：按立面后主导功能生成窗墙比 / 挑檐建议（三条规则，全部由配置表区间驱动），每条带试算效果和「采纳」按钮；采纳只改一个参数、不连锁。自检 48 项。记录在 `Version_04/PLAN_v04.md`。
- V02 只在自检部分加了 `digest()` 数值摘要与 `wwrSelfTest()` 包装；V02 / V03 / V04 摘要逐字符相同，原有四维度数值未变。

**Key decisions**
- 新功能只读 `calc()` 结果，不改任何现有计算函数。
- 配置表用 JS 文件而不是 JSON：双击打开的网页读不了本地 JSON。文件缺失时页面提示，其余功能照常。
- 房间进深 D 以外的格子不计采光和得热（与"D 处有内墙"一致）；服务区自然落在中部。
- 格子取范围内解析平均而非中心采样，保证房间带平均严格一致。
- 分配算法无随机数、无历史依赖；连片强度按格边长换算，结果与网格尺寸无关。
- 解释句比较"加权贡献"而不是分数本身，并区分被平滑 / 面积 / 连片改动的情况。

**Current state**
- `Version_03/`：wwr-tool.html + zoning-config.js + PLAN_zoning.md（A + B，已验证）。
- `Version_04/`：wwr-tool.html + zoning-config.js + PLAN_v04.md（A + B + C，自检与界面点击测试通过，待用户在 Chrome 验证）。
- 内置浏览器打开本地文件是静态快照，不加载旁边的 zoning-config.js，也丢 `?test=1`；测试时用控制台注入配置并调用 `wwrSelfTest()`。用户在 Chrome 双击打开则正常。

**Unresolved**
- 配置表所有阈值、权重、面积占比是设计判断值。北向房间带被划为卧室而非服务区（服务区落在中部无光区），若想服务区优先占北侧需下调服务区采光曲线上限。
- 建议只动窗墙比和挑檐；采纳一条后可能出现拉锯式的新建议（加挑檐 → 采光降 → 建议加窗），由用户判断。
- 办公室、社区中心两种用途尚未做；需要补的字段见 PLAN_zoning.md §11。

**Next session: suggested starting point**
- Chrome 打开 `Version_04/wwr-tool.html`，看三条建议、点采纳、观察分区变化。
- 候选方向：写办公室配置表试切换用途；把相邻关系接进分配代价；或回到 PHPP 核实热质量档位。
