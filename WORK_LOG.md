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

---

## 2026-09-24（session 3；Version_05 界面整理）

**Completed**
- 写 `Version_05/PLAN_v05.md`（现状、每项改动的结构 / 样式 / 函数、主区新排列示意、去重规则、三处同步方式、验证方法、9 项决定）。用户决定分区面板旋转建筑，其余按推荐。
- 复制 V04 为 V05，只改界面：各立面改为标签页（名称 + 方位角 + 窗墙比 + 建议圆点，方向键切换，与日照图 / 表格 / 分区面板四处同步，采纳后自动切到该立面）；左侧栏桌面端 sticky；新增独立「室内分区」面板（大比例、随朝向旋转、四边立面标签、指北针、图层切换 / 图例 / 格子详情在右列），原日照图去掉方格；「分区建议」与「设计提示」合并为「设计建议」（可采纳项在前，同立面同类去重，筛选全部 / 仅所选立面）；剖面角度标注避让；气候按钮短标签；汇总行竖排小卡、≥1280 px 一行；底部说明改为折叠的六段「计算方法说明」。
- 验证：V04 / V05 计算摘要与界面文本摘要（汇总、表格、详情、分区、格子、建议、去重前提示）逐部分哈希相同；自检 60 项通过；1440 / 390 px 截图存 `Version_05/screenshots/`；真实按键验证方向键切换标签。
- V04 只在自检里加了 `uiDigest()`。

**Key decisions**
- 去重按「同一立面 + 同一问题类别或同一动作」，保留带「采纳」的那条；默认方案删 4 条提示。
- 提示的类别由文字特征识别（`tagTip`），提示文字本身不改。
- 分区面板旋转建筑（用户选择），viewBox 按对角线留空；立面标签字号按面板像素宽换算保持约 12 px。

**Current state**
- `Version_05/`：wwr-tool.html + zoning-config.js + PLAN_v05.md + screenshots/。待用户在 Chrome 验证。
- 自动化工具注入的 Enter / 空格不会激活原生按钮（对任何按钮都如此），图层按钮和「采纳」的键盘激活未能用工具验证，请用户在 Chrome 里 Tab + Enter 确认。
- Edge 无头截图：系统深色模式 → 截图为深色主题；窗口最小宽度 > 390，390 px 截图用 iframe 包装页渲染。

**Unresolved**
- 手机 375 px 下分区格子 11.6 px（旋转视图按对角线留空所致），1440 px 下 23 px 达标。
- 格子的键盘操作未做。

**Next session: suggested starting point**
- Chrome 打开 `Version_05/wwr-tool.html`：试标签页、分区面板、合并后的建议列表；用 Tab + Enter 试图层按钮和「采纳」。
- 候选方向：办公室配置表；相邻关系；格子键盘操作。

---

## 2026-09-24（session 4；Version_05 第二轮：平面图合并 + 信息图层）

**Completed**
- 用户验证第一轮通过（采纳按钮键盘可用）。写第二轮方案（合并两张平面图、信息图层可开关），用户要求直接在 V05 做并记入 PLAN_v05.md；方案并入该文件，撤掉临时的 Version_06 文件夹。
- 实施：「室内分区」与「平面与日照方位」合并为一张米制坐标的「平面」（建筑随朝向旋转；罗盘环、日照弧线、净得失色带、窗与挑檐、立面标签、房间带边线各为信息图层，原生复选框开关，状态记在 localStorage）；关掉日照方位后图自动放大；剖面与所选立面详情并排。自检 70 项；数值与界面文本摘要与 V04 一致；截图更新。
- 修了两个实施中的回归：状态对象少一个逗号导致整页脚本不加载（用 Edge 无头 `--enable-logging=stderr` 拿到行号）；新的两列规则覆盖窄屏单列规则。
- 用户在 Chrome 验证后反馈两点并已修：所选立面的黑色边线盖住窗线 → 只靠标签加粗表示；点击立面出现大块焦点框 → 点击区与标签不再可聚焦。

**Key decisions**
- 一张图、一个坐标系（米），旋转组与世界坐标分层；信息图层关掉即不输出元素，方便自检断言。
- 记忆只记图层开关，不记任何设计参数；无 localStorage 时静默用默认值。

**Current state**
- `Version_05/` 为最新可用版本（A+B+C + 两轮界面整理）。待用户在 Chrome 验证第二轮。

**Unresolved**
- 手机宽度下格子约 10–12 px；朝向偏转 45° 附近立面标签可能靠近罗盘文字。

**Next session: suggested starting point**
- Chrome 打开 `Version_05/wwr-tool.html`：开关各信息图层，看关掉日照方位后的放大效果，刷新页面确认开关被记住。
- 候选方向：办公室配置表；相邻关系；格子键盘操作。

---

## 2026-09-25/26（被动房工具 Version_06：功能适宜度图）

**Completed**
- 读完 V05 工具、配置表、PLAN_v04 / PLAN_v05，写出 `Version_06/PLAN_v06.md`（8 节 + 11 个决定项），用户要求先做一版看效果。
- 复制 V05 为 V06（先提交 952d99b），实施：立面标签页移到侧栏顶部；底图「分区」改「适宜度」（总览按最高分功能着色、深浅按领先幅度；各功能热力图；选项由配置表生成）；删除 `assignZones`、`stripDominant` 与连片 / 面积分配；面积占比改为反馈；卧室加 `needsWindow`（房间带以外 0 分，默认影响 20 格）；每个立面面板加「这一侧打算放置」下拉，V04 三条建议规则改用设计者指定，未指定只显示参考功能与引导句；新增「指定功能适合度偏低（含主因）」与「适合面积低于目标」提示；房间带图层按指定功能填色、转角对角线分割；文字全部改为「功能适宜度」定位。
- 验证：`digest()` 与 V05 逐字符相同；汇总行 / 指标表 / 详情面板哈希相同；适合度分数在 700 个未受影响组合上与 V05 一致（用临时副本导出比对，副本未入库）；自检改写 14 项、新增 30 项，共 100 项通过；真实键盘按键验证下拉可用；375 px 无横向滚动；截图在 `Version_06/screenshots/`。
- 提交 68dbe42，已推送。V05 未改动。

**Key decisions**
- 决定项 1–11 按推荐；needsWindow 按用户原文只看房间带几何。
- 主因算法由计划的「与最适合功能比较加权贡献差」改为「让指定功能失分最多的条件」（前者回答的是"另一功能为什么赢"）；格子级解释句保留原算法（问题不同）。
- 领先幅度映射 alpha = 0.10 + 0.50·min(m/25,1)，10 分以下算「多种可能」；偏低阈值 平均 < 50 或落后 ≥ 15。

**Current state**
- `Version_06/wwr-tool.html` + `zoning-config.js`（version 2）可双击打开；默认方案机场站当下：适合面积 客厅 39% / 卧室 44% / 服务区 17%（低于目标 20–35，已提示）；领先幅度 < 10 分的格子 16.3%。

**Unresolved（等用户在 Chrome 看过后决定）**
- 偏低阈值：当下气候西侧指定卧室为 71 分、落后客厅 14 分，按 15 分阈值不提示，2080 年才提示；改 `FIT_GAP` 为 10 则当下提示（南侧也会）。备选：14 分档用「略低」措辞。
- needsWindow：窗墙比为 0 的立面，其房间带对卧室仍约 50 分；改为只计有窗立面的房间带是一行改动。
- 是否推送后继续在 V06 上调整，或定格 V06 再开 V07。

**Next session: suggested starting point**
- Chrome 打开 `Version_06/wwr-tool.html`，看总览深浅、指定西立面为卧室、切 2080 年，检查提示是否符合直觉。
- 定阈值与 needsWindow 判定方式后一行改动 + 重跑自检。

---

## 2026-09-26（Version_07：照片 → Rhino MCP → Grasshopper ↔ WWR 工具 同步链路，prototype 完成第 1–5 步）

**Completed**
- 用户提供 `PLAN_v07.md`；解读后补了一处不自洽（窗位置也需 `base_x` 存原始值，与 `base_width` 同样处理），用户接受。复制 V06 为 V07。
- 电脑没有系统 Python，经用户确认用 winget 装了 Python 3.12（仅当前用户）。
- 第 1 步：手写 `rhino/windows.json`；Rhino 8 由 MCP 自动启动，建 `Facade` 墙面；通过 MCP 搭 Grasshopper 定义 `wwr_sync.gh`（Trigger 0.5 s → 读文件 + 换算 + 生成预览 + 写回 的 Python 3 脚本 → 面板；Toggle → 替换式 bake 脚本）。改文件后 363 ms 写回，窗宽与手算一致。
- 第 2 步：bake 三次各 2 个对象、无重复；修了「GH 传的是几何编号不是几何」。
- 第 3 步：`rhino/server.py`（标准库）+ `start_server.bat`；页面加连接状态、「绑定到 Rhino」下拉、「读取 / 同步」按钮、打开自动读取；自检 100 → 106；`digest()` 与 V06 逐字符相同。
- 第 4 步：60% → 停在几何上限 8.47%，读取后滑块回落 8%。
- 第 5 步：用户给照片（小木屋效果图，五扇竖长窗）+「窗高 2 m」；目测估计立面 4.3 × 2.85 m、窗 0.50–0.52 × 2.0 m；替换手写文件后全链路复测通过，上限 57.7%、下限 24.9%。
- 修了时间戳只到秒的问题（同一秒两次写入被 GH 当成没变）：server.py 与 GH 脚本都改为带毫秒。
- 提交：ec705bc（第 1–3 步）、7349b1e（忽略 .3dmbak）、ef2c0f7（第 4–5 步）。

**Key decisions**
- 「读文件」与「换算 + 生成」合成一个 GH 脚本；用 `updated_at` 字符串判断变化，写回后记住自己的时间戳避免自触发。
- 窗面比墙面往外 2 cm 避免重叠闪烁。bake 只在开关由关到开时执行一次。
- 自检模式（`?test=1`）不自动读取 Rhino，保证 `digest()` 可与 V06 比对。
- 状态文字放页首标题下；绑定下拉放「各立面」顶部（只有一面墙，一个绑定）。

**Current state**
- 一切可复现：双击 `Version_07/rhino/start_server.bat` 起服务并开页面；Rhino 打开 `facade.3dm`，Grasshopper 打开 `wwr_sync.gh`。`.claude/launch.json`（内置浏览器起服务用，含本机绝对路径）未入库。
- 用户结论：prototype 已证明整个流程可行。

**Unresolved**
- 第 6 步（演示脚本 + 录屏）需用户亲手操作；可先由 Claude 写一页操作清单。
- MCP 的 Python 3 组件加参数后必须调 `VariableParameterMaintenance()`，否则新输出为空（已记入 memory）。
- 留到成品：多立面、BCBC `max_wwr`、`scale_mode` 其他分配规则、透视校正、真实尺寸是否回灌热工计算。

**Next session: suggested starting point**
- 起服务、开 Rhino + GH，按 PLAN_v07 §6 走一遍演示并录屏；或直接开始讨论成品阶段的范围。

---

## 2026-09-30 → 10-02（Openning_Shade_Relation_Tool：Strip Window 遮阳推敲器 → 机构库 → Massing_v01 第一刀）

**Completed**
- Strip Window 页面（`Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/`）：铝板厚度、投影遮阳率与视野通透率；接入共享引擎（朝向、进深、气候、热质量、通风 → 四面与整栋的过热 %、采光系数、冬季净得热）；标准层平面热力图（过热 / 采光两层、有板 / 无板、板后板间光斑）；孔径 + 孔距 → 穿孔率，表皮厚度 → 漫射光孔壁因子；逐板随机穿孔率。
- 共享引擎 `_shared/wwr-engine.js`：段级 `screen / screenDay`；每扇窗可带 `screen / screenDay / oh / ohIn / ohGap / ohOpacity`（部分窗在屏后、部分在翻开的板下）。缺省与 V06 逐位相同（自检 49 项、1608 字段比对不变）。
- 规则与库：`02_Rules/SHADING_RULES.md`（八问拆解、分类、调节逻辑、参数卡、六段流程）、`02_Rules/MECHANISMS.md`（机构库记录）。机构库 `MECH` 四个条目：#0 中轴转动板、#1/#2 膝盖式折板（竖轴 / 横轴，折角唯一状态参数；第一次按"门式开合"理解错，用户纠正为两端固定中间凸）、#3 伞式六角折板（Al Bahar 动态分析图）。换装置不碰引擎与页面的过热 / 采光路径。
- UI：侧栏按建筑与环境 / 装置类型（固定）/ 装置与建筑的关系 / 装置本身折叠分组；平面与数据两张可拖动、可改宽、可收起的浮窗；界面状态记在浏览器，设计参数不存。
- Massing_v01（`Strip_Window/Massing_v01/`，PLAN_massing_v01.md 第 2 稿）第 0–6 步：`rhino/server.py`（8768，字段校验，`/shared/` 转发引擎）、`state.json` 契约、`massing.3dm`（Handles 图层一个手柄点）、`massing.gh`（Trigger 0.5 s → Python 3「massing sync」→ 面板；源码在 `massing_sync.py`）、`massing-tool.html`。环路验证：页面滑块 → json → GH 周界（矩形减凹口，三层同形）→ 立面段写回 → 页面引擎逐段过热 / 采光、无凹口对照、平面图、模板解读；Rhino 拖手柄 → json → 页面滑块同步并标「来自 Rhino」。边界：深 0 → 4 段；凹口贴端点 → 零长段剔除（7 段）；换边 B 正常；自检 8 项通过。
- 提交：489dc09、6c21be9、f069289、7263535、ec0b5a2、8eb4aea（Strip Window 与引擎）；Massing_v01 本次提交。

**Key decisions**
- 参数走文件桥，Claude 不在每次参数变化的回路里；只做读图填卡与结果解读（两份架构文档的一处有意差别）。
- 遮阳第一刀不做，机构库条目第二刀移植到 GH；Ladybug（已安装）作为第二口径在第 7–8 步接入；第一刀指标用共享引擎。
- 手柄与滑块冲突：`ops.at` 与 `handle.at` 比时间戳，后动者算数。
- 机构库"一个例子写专条，两个例子归成族"。

**Gotchas**
- MCP 的 Python 3 组件：`SetSource()` 设源码，`CreateParameter + RegisterOutputParam + VariableParameterMaintenance()` 加输出；**`MarshOutputs` 默认 False，Python 列表会被当成一个对象，必须设 True**。Trigger 用 `AddTarget(guid)`，`Interval` 毫秒。保存用 `GH_DocumentIO(doc).SaveQuiet(path)`。
- GH 从 Rhino 文档读点、`Objects.Replace` 移点都可在脚本内做；不需要引用式 Point 参数。
- 手写 json 时间戳不要晚于机器时钟（曾因 2026-10-02 的手写戳让手柄一直"更新"）。
- `get_viewport_image` 返回体过大时改用 `view.CaptureToBitmap().Save()` 落盘再看。
- 本地静态服务（8767 / 8768）偶尔随面板关闭而停，重开即可；页面经 http 打开才能读共享引擎。

**Current state**
- Massing_v01 可复现：双击 `rhino/start_server.bat`；Rhino 打开 `massing.3dm`，Grasshopper 打开 `massing.gh`；页面 `http://localhost:8768/`。
- 共同近似见 MECHANISMS.md；竖鳍的角度效果、平面网格的"找最近墙段"、动态调节规则未做。

**第 7–8 步（同日续）**
- Ladybug 已装；`LB Cumulative Sky Matrix` 报「No Radiance installation」，入射辐射做不了 → 改用 `LB SunPath + LB Direct Sun Hours`（纯几何，不含云）。链：sync 输出 epw 路径（随页面气候选择）/ north / m0 m1 / winMesh（每扇窗条沿长度 ~1 m 一格的网格，法线朝外）/ winFaces / nSeg → LB Import EPW → LB Analysis Period → SunPath（hoys、north_）→ Direct Sun Hours（_grid_size 必填，给了滑块 1.0；context = 楼板；_run = Toggle）→「massing sun」Python 按面数归到窗、按「窗序号 % 段数」归到段，写回 `results.sun {period, unit:h, perSegment, perWindow, at}`。
- sync 写回时若几何与分析期没变则保留上次的 `sun`；sun 写回脚本在文件缺 `sun` 时也重写。
- 页面：段表加「直射日照」列（按分析期标题，颜色随值），分析期下拉（夏 / 冬 / 全年）与气候一起写进 `run`，解读多一句（最多 / 最少 / 凹口内各段）。验证：夏季 A1 887 h、凹口两侧 A2 423 / A4 385、北 523；切冬季 ≤ 10 s 刷新，北 0 h、南 806 h。
- Gotchas：`SetSource()` 之后 `MarshOutputs` 会被重置为 False，每次重载源码都要再设；页面与服务字段同时改时要重启本地服务（旧进程还在跑旧校验，会悄悄丢字段）。

**第二刀第 1 项（同日续）：竖轴膝盖折板进 Grasshopper**
- json 加 `shading` 参数卡（type / unitW / tilt / standoff / thick / skin / holeD / perfMin / perfMax / floors / fixed），服务校验。
- `massing_sync.py` 的 `device_units()`：每层每段从中间排满单元（n = ⌊段长 / 单元宽⌋），固定边交替，两片各一张竖向面片（折角决定膝盖位置），输出 `devMesh`（3 层 × 30 单元 × 2 片 = 180 片）接 Direct Sun Hours 的 context（与楼板并列两个来源）；翻译结果按段写回 `dev = {screen, screenDay, view, units}`，规则与 Strip Window 页面相同（投影、逐板随机穿孔、孔壁因子）。
- 页面：「遮阳装置」分组（装置 / 覆盖层 / 折角 / 单元宽 / 离墙 / 板厚 / 表皮 / 孔径 / 穿孔率上下限）；段表改为 视野 · 过热无板/有板 · 采光无板/有板 · 日照；整栋无板→有板两行；解读多一句；自检 +2（10 项通过）。
- 验证（凹口 A 深 4）：45° 时整栋过热 6.0 → 0.2 %、采光 3.6 → 1.4 %、视野 30 %、南向日照 887 → 560 h；0° 时过热 0、采光 0.7 %、视野 7 %、南向日照 196 h。
- Gotcha：服务字段改了必须重启本地服务；页面在服务停掉期间会刷出一串 ERR_CONNECTION_REFUSED，恢复后自愈。

**第二个拓扑操作：庭院（同日续）**
- `ops` 支持第二条 `court`（pos_u / pos_v / width / depth），服务校验；Rhino `Handles` 图层加蓝点 `court01`（庭院中心），手柄逻辑按 op 类型通用化（HANDLE_KEYS）。
- `massing_sync.py` 重写为外圈 + 内圈：内圈顺时针，(dy, −dx) 指向天井即内墙"室外"方向，段名 Y1–Y4，朝向、窗条、折板、日照网格全部沿用；楼板实体 `Extrusion.AddInnerProfile`。
- **坑**：内轮廓逐层平移后 2 层以上的洞丢失（AddInnerProfile 只认轮廓平面上的曲线），症状是庭院内墙日照全为 0；改成 z=0 做一次实体再 `Translate` 逐层。诊断方法：取窗条网格面心沿法线偏 0.1 m，`IsPointInside` + `RayShoot` 朝太阳。
- 页面：拓扑操作组分凹口 / 庭院两块，庭院有开关、中心 u/v、宽、深；段表多 4 行内墙；平面画洞和蓝点；解读多一句。验证（庭院 6×6，无装置）：Y1 北 20 h、Y2 东 266 h、Y3 南 419 h、Y4 西 239 h；过热 Y4 9.8 %、Y3 9.2 %。

**其余三个机构条目进 GH（同日续）**
- `massing_sync.py`：`device_units` 改为按 `shading.type` 分派：`dev_pivot`（单片绕中轴转，正负交替）、`dev_bifoldV`、`dev_bifoldH`（两片横向折板，顶边固定；写回 `kind:'knee'` + c / fA / gapH / D / tS / tD）、`dev_umbrella`（六角伞，中心 + 6 角点 + 6 折痕点，12 三角面；覆盖率用与页面相同的六角星采样）。面状类统一走 `_areal()`。
- 页面：下拉四条目 + 无装置，每条目自己的滑块文字和说明；引擎侧横轴折板把窗拆成屏后 / 挑檐下 / 无遮三组（引擎每扇窗的 oh / ohIn / ohGap / ohOpacity 字段派上用场）；自检 +2（12 项）。
- 验证（凹口 + 庭院，45°，单元 3 m，夏季南向 A1 直射日照）：无装置 887 h → 中轴转动板 437 h、竖轴折板 376 h、伞式六角 428 h、横轴折板 211 h（膝盖挡高角太阳最狠）。
- 坑：在 `run_python` 里 `time.sleep` 会卡住 Rhino 主线程，GH 的 Timer 不会跑；要等 GH 反应必须从外面（Bash）改文件再等。

**U 形 + 移边 + 楼层组（同日续）**
- 三件合一：楼层组 = `building.groups {podium, setback{A,B,C,D}}`（第 1 组基底矩形，第 2 组四边各退 = 退台 / 上部移边）；操作带 `apply: all/g1/g2`；U 形 = 凹口深度上限改为对面墙前 WALL。
- `massing_sync.py` 重写：`floor_rect(b, i)` 给每层矩形与组号，`edges()/notch_limits/court_rect/notch_rect` 全部按矩形 (x0,y0,x1,y1) 工作；每层各自周界、洞、段（带 floor）、窗条、折板；`results.floors[]` 带 rect / group / perimeter / holes / area，`results.segments` 扁平带 floor，窗条网格与段一一对应（日照写回按序归段，不再用取模）。手柄仍按第 1 层矩形解释。
- 页面：建筑组加「楼层组」块（裙房层数、A–D 退台）；凹口 / 庭院各带「作用在」；段表按层筛选、段名带 F#；平面可选层、其他层虚线叠出；引擎每段 floors=1，整栋按房间面积加权；解读加楼层组句和 U 形提示；自检 12 项（zoneA 改为单层）。
- 验证：裙房 2 层 + 顶层 A/C 各退 3 m + 庭院只作用第 1 组：各层面积 420 / 420 / 276 m²，32 段；凹口深 12 m（U 形）正常。
- 坑：解读函数里 `const` 的使用顺序（f1 在定义前被用）→ 页面静默回到「等待数据」；用 window.onerror 抓到。

**收尾（同日）：逻辑缺口盘点**
用户问"整个工具成立逻辑上还有哪些功能没做"，答复按重要程度：
1. 真正的逻辑缺口：体量自遮挡没进过热计算（引擎每段只看朝向，凹口 / 庭院 / 退台互挡只在 Ladybug 日照里）；日照小时与过热 % 两套数字没接起来；引擎城市预设与 EPW 是否同一地点没有检查。
2. 关系不完整：装置按立面 / 按组分设；窗墙比按立面分设；室内分区没跟平面变（先做"每格找最近墙段"）；装置是静态的，无随时间开合规则；没有方案对比。
3. 可用性：无一键启动；结果不能导出；读图填卡没接进网页；引擎数字只宜比大小，解读里应写明。
建议顺序：自遮挡进过热 → 装置按立面分设 → 方案对比。
关机前状态：Rhino / GH / state.json 已存；凹口此时在 B 边 pos 0.39（用户拖过手柄），庭院只作用第 1 组，顶层 A/C 各退 3 m，竖轴折板 45°，32 段，日照结果齐全。

## 2026-10-03 — Massing_v01：体量自遮挡进过热

- 规则：每段 `expo` = Ladybug 直射日照小时（遮挡只有楼板）÷ 同朝向自由墙面的小时；引擎 `seg.expo` 只折减直射，缺省 1 与 V06 逐位相同（engine-test 49/49 仍过，版本 2026-10-03）。
- GH：复制一个 LB Direct Sun Hours（`SunHoursMass`，context 只接 floors）；`massing sun` 加输入 `resMass`、`vecs`；`massing_rad.py` 重写，自由墙面小时 = 太阳向量里照得到外法线的个数（SunPath 向量从太阳指向地面、只含地平线以上，timestep 1）。写回 `results.sun.massOnly / free / expo`。
- 页面：`calcSegs(segs, winH, withDev, expo)`；段表加「受晒」列（≥90 绿 / ≥60 黄 / 其余红）；解读加自遮挡句；自检 +3（15 项）。
- 验证（凹口 B 边 + 庭院第 1 组 + 顶层 A/C 退 3 m，夏季）：凹口内 B2/B3/B4 受晒 47 / 63 / 56 %，庭院四壁 0 %（被顶层盖住，物理上对），其余 100 %；整栋受晒 81 %。
- 气候一致性：`massing_sync.EPW[clim]` 与 `CLIM[clim].file` 是同一个 EPW 文件名，三个气候都对上，不需要运行时检查。
- 坑：
  - LB 组件都是 GhPython（同一个 ComponentGuid），**不能用 ComponentGuid 找 LB 组件**，我按它删掉了 ImportEPW / AnalysisPeriod / SunPath，靠从磁盘重开 massing.gh 救回。只按 InstanceGuid 或 NickName 找。
  - LB 组件会在脚本里自己改 NickName，`SunHoursMass` 这个昵称跑一次就变回 `DirectSunHours`；记 InstanceGuid（55422f50…）。
  - 复制 LB 组件：`GH_DocumentIO.Copy(Local, True)`（按选中）→ `Paste` → **`Document.MutateAllIds()`** → `MergeDocument`；不 Mutate 会因 InstanceGuid 重复而炸，而且会留下同 guid 的幽灵对象。
  - `EmitObject(ComponentGuid)` 生成的是空的 Python 组件，没有 LB 的脚本和端口。

**装置按立面分设（同日续）**
- json：`shading.facades = {A|B|C|D|court: {on, tilt}}`；server 校验（键只许这五个，tilt 0–90，on 布尔）；缺省 = 全装、默认折角。
- `massing_sync.py`：`facade_key(seg)`（外圈取边名首字母，庭院内墙 = court）、`facade_setting(sh, seg)`；生成时每段复制一份 shading 换成自己的折角，不装的段 `dev = NONE`；`results.shading.facades` 回显。
- 页面：装置卡加 `#facTable`（勾 + 滑条 + 读数，不装的行变淡）；默认折角滑条的 input 监听先把五个滑条设成同值，再走通用监听；立面标签带朝向（A（南）…随 az0 变）；g4 摘要 `A45 B45 C— D70 庭45`；解读句按立面列。
- 验证：C 不装、D 70°：C 段 units 0、视野 100 %、过热有板 = 无板；D 段 5 单元 @70°、视野 59 %、过热 9.6 → 3.3 %；日照重算（装置几何变了）。整栋 4.3 → 0.4 %。
- 服务改了 server.py 要重启：先 `Get-CimInstance Win32_Process` 看 PID 命令行确认是 `python server.py`，再 Stop-Process，然后 preview_start massing-bridge。

**平面热力图（同日续）**
- 用户先问"方案对比之后还有什么"，答：窗按立面分设、室内一侧（热力图 → 房间）、父子比例、动态调节、散射的自遮挡、可信度说明、Radiance、一键启动、导出、读图填卡。用户选先做平面热力图（"对设计价值最大"），我回答：值最大，但它是分布图不是房间模拟。
- 页面 `planGrid`：所选层楼板铺格，每格对每段墙按 V06 的核（`kernelCell` 衰减 + `sunPatch` 直射条带）取值，条件 = 垂足在段内、在内侧、≤ 进深、连线不穿庭院；多段相加；记主要来源段与离墙距离；房间带外的格灰显。平面卡加模式（过热暴露 / 采光 / 只看段）与格距（0.5 / 1 / 2 m）；格有 title 提示。解读加一句。自检 19 项。
- 验证：F3（10 × 30 退台层）全在房间带内，过热暴露最高在 D 边后 1.5 m（11.8 kWh/m²，D 折板 70° 最开）、最低在 A 边后 4.5 m（折板 45°）；F1 带庭院：庭院四周格由内墙供值，庭院挡住的格不取外墙。
- 坑：解读函数里已有 `const G`（楼层组），再声明一个 `G` 整页静默失效（SyntaxError 只在控制台）；改名 `PG`。控制台的旧错误在导航后仍留着，看时间顺序。

**Grasshopper 预览配色（同日续）**
- 用户：红色透明体块看不清。加三个 Custom Preview（`preview floors / windows / devices`），材质直接写在 M 端的 PersistentData（`GH_Material(Color)`）：楼板 (228,224,214) 不透明、窗条 (80,150,230) α150、装置 (196,104,38) 不透明。`massing sync` 和两个 LB Direct Sun Hours 的组件预览设 Hidden（LB 的日照色网格与窗条同面会闪烁；要看日照色时右键该组件 → Preview 打开即可）。截图 `screenshots/rhino_preview_colours.jpg`。

**Next session: suggested starting point**
- 方案对比（存几个状态并排看）→ 窗按立面分设 → 父子比例、动态调节规则、单文件打包、Radiance、可信度说明。
