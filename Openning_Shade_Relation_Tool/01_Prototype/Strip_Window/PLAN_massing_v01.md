# Strip Window · Massing_v01 计划：体量拓扑 × 立面分段 × 环境反馈（第一刀，第 2 稿）

日期：2026-10-02。状态：计划，未开始修改代码。整合自用户提供的两份文档《AI-Assisted Environmental Massing Workflow — Implementation Architecture v2》和《Topology Operations + Multi-Floor Interaction》，并接到现有的 Strip Window 工具、V07/V08 的 Rhino 桥接和共享引擎上。

第 2 稿按用户意见改了两点：**遮阳用机构库的装置，不用挑檐**（放到第二刀）；**Ladybug 未安装，第一刀的指标用共享引擎**（过热 %、采光系数），Ladybug 以后作为第二种口径接入。

**位置**：新工具放在 `Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/`，现有的 `Strip Window · 立面表达工具.html` 不动。

---

## 0. 一句话架构与分工

> 建筑师在 Rhino 里拖手柄改体量；网页定义"对哪几层、做什么操作、怎么传播"；json 文件是唯一的状态；Grasshopper 读 json 生成楼板和立面段，写回每段的长度和朝向；网页用共享引擎算每段的过热与采光；Rhino 显示几何；Claude 只做两件事：读图片填遮阳参数卡，把结果翻译成设计语言。

| 层 | 负责什么 | 现有基础 |
|---|---|---|
| `state.json` | 楼层、操作记录、窗、运行请求、手柄回流、立面段结果 | V08 的 `windows.json` |
| `server.py` | 网页 ↔ 文件 | V08 的 `server.py`（标准库，毫秒时间戳） |
| `massing.gh` | Python 组件：读 json → 周界 → 楼板预览 → 立面分段 → 写回 | V07/V08 的脚本 |
| Rhino | 手柄可拖（GH 引用），几何只看 | V07 的 bake 改为「手柄 + 预览」 |
| 网页 | 建筑、操作、窗；运行；立面段的过热与采光表；模板解读 | Strip Window 的侧栏分组、浮窗、过热 / 采光表 |
| 共享引擎 | 每段墙 `{len, az, windows}` → 过热 %、采光系数；整栋按房间面积加权 | `_shared/wwr-engine.js`，已支持任意朝向的墙段 |
| Claude | 读图填卡、结果解读（第一刀都不接） | SHADING_RULES.md |

**与两份文档的一处不同（有意的）**：参数走文件桥，Claude 不在每次参数变化的回路里。工具在没有 Claude 会话时也能用。

---

## 1. 第一刀的范围

| 项 | 第一刀 | 明确不做 |
|---|---|---|
| 体量 | 3 层矩形基底（长、宽、层高、朝向来自网页） | 退台、错位、竖向中空、分裂 |
| 拓扑操作 | 一个 **凹口（Notch）**：指定边、位置（沿边 0–1）、宽、深 | 庭院、U 形、移边、移角 |
| 楼层关系 | 从 F1 起 **向上传播**（三层同形） | 独立层、父子比例、楼层组 |
| Rhino 手柄 | 一个点：凹口中心；拖它改位置和深度 | 多手柄、边拖动 |
| 立面 | 周界每条边一段，自动算朝向；每段一条通长带窗 | 逐扇窗 |
| 遮阳 | **无** | 机构库条目（第二刀移植到 GH） |
| 指标 | 共享引擎：每段过热 %、采光系数；整栋加权 | Ladybug（装好后接入）、平面热力图（网格要改为"找最近墙段"） |
| 网页 | 建筑、凹口、窗三组滑块；同步；立面段表；模板解读；手柄回流 | 图片识别、楼层组界面、室内分区 |

第一刀要证明的一句话：**拖 Rhino 手柄或改网页滑块 → json 变 → GH 重算周界与立面段 → 写回 → 网页用引擎算出每段过热与采光 → 数字变**。

---

## 2. 文件结构

```
Strip_Window/
├── Strip Window · 立面表达工具.html     ← 不动
├── PLAN_massing_v01.md                    ← 本文件
└── Massing_v01/
    ├── massing-tool.html
    ├── rhino/
    │   ├── server.py
    │   ├── start_server.bat
    │   ├── state.json
    │   ├── massing.3dm                    ← 图层：Handles（手柄点）/ Preview（GH 预览，不 bake）
    │   └── massing.gh
    └── screenshots/
```

---

## 3. `state.json` 契约

```json
{
  "updated_at": "2026-10-02T10:00:00.000",
  "building": {"floors": 3, "H": 3.0, "L": 30, "W": 16, "az0": 180},
  "ops": [
    {"id": "notch01", "type": "notch", "floor": 1, "propagate": "up",
     "edge": "A", "pos": 0.4, "width": 6, "depth": 4, "at": "…"}
  ],
  "windows": {"wwr": 0.45, "sill": 0.73},
  "run": {"seq": 3},
  "handle": {"notch01": {"pos": 0.42, "depth": 4.5, "at": "…"}},
  "results": {"seq": 3, "at": "…",
    "floors": [{"i": 1, "area": 456.0, "perimeter": [[0,0],[30,0],…]}],
    "segments": [{"floor": 1, "edge": "A1", "az": 180, "len": 12.0, "u0": 0, "u1": 12.0}],
    "warnings": []}
}
```

- 网页写 `building / ops / windows / run`；GH 写 `handle / results`。谁写谁的字段。
- 手柄与滑块的冲突：`ops[].at` 与 `handle[].at` 比时间戳，**后动的算数**；网页收到更新的 `handle` 就把滑块同步过去并提示"来自 Rhino"；网页改滑块就写 `ops` 并更新 `at`。
- 边名：基底四边 A/B/C/D，A 朝向 = `az0`，顺时针递增。凹口把一条边切成多段，命名 `A1, A2, A3`（沿边从左到右，从室外看）；凹口的两条侧边朝向 = 原边朝向 ± 90°，底边朝向 = 原边朝向。
- 引擎输入由网页拼：每段 `{len, az, oh:0, windows:[{w:len, h:winH, sill}]}`，`winH = wwr × (H − 楼板厚)`；房间进深、气候、热质量、通风仍在网页上选。

---

## 4. Grasshopper 定义（massing.gh）

1. **Timer 0.5 s → 读 json**：`updated_at` 变了才动作；写回后记住自己的时间戳避免自触发（V07）。
2. **周界**：矩形减凹口 = 多边形，Python 自己算顶点（凹口宽截到边长、深截到 W/2 或 L/2）；向上传播 = 三层同一个多边形。
3. **楼板预览**：三层楼板 Brep，GH 预览（不 bake）；可选一个开关 bake 到 `Preview` 图层做截图。
4. **手柄**：Rhino `Handles` 图层上一个点，GH 引用；点到所选边的投影 → `pos`，点到边的垂直距离 → `depth`（限 0 到 W/2）。手柄移动 → 写回 `handle`；若 json 的 `ops` 时间戳更新 → GH 反过来把手柄点移到 `ops` 对应位置（用 MCP 的 Rhino 脚本或 GH 的点更新）。
5. **立面分段**：周界每条边一段，外法线方位角，`u0 / u1` 为沿原边的坐标。
6. **带窗预览**：每段一个矩形面（窗条），帮助在 Rhino 里核对朝向与段划分。
7. **写回**：`results.floors / segments / seq`。

组件尽量少，逻辑在 Python 组件里。MCP 的 Python 3 组件加参数后要调 `VariableParameterMaintenance()`。

---

## 5. 网页（massing-tool.html）

- 从 Strip Window 复制样式与分组骨架；去掉三维视图（几何在 Rhino 里看），主区放两张浮窗：**立面段表**、**解读**；侧栏三组：建筑（长、宽、层数、层高、朝向、窗墙比、窗台；进深、气候、热质量、通风）、凹口（边、位置、宽、深；传播固定"向上"灰显）、同步（状态、同步按钮、最近结果 seq）。
- 任何滑块变 → 写 json（`ops.at` 更新）→ 轮询 `results.seq` ≤ 5 s → 收到段表 → 引擎逐段算 → 表格刷新。
- 立面段表：段、朝向、长度、窗面积、过热 %（着色，判据同 Strip Window）、采光系数；整栋按房间面积加权一行。
- 解读：模板句，例如"凹口把 A 边切成 A1 / A2 / A3，新增的两段朝向 90° 与 270°；过热最高的是 ××（×× %）"。不接模型。
- 手柄回流：收到 `handle` 时间戳新于 `ops` → 滑块同步并标"来自 Rhino"。
- 自检（`?test=1`）：固定一份 `results` 样本，引擎结果与手算一致；边界：凹口深 0 时段数 = 4，凹口到边端时段数 = 6。

---

## 6. 实施顺序

| 步 | 做什么 | 完成标准 | 需要你 |
|---|---|---|---|
| 0 | 建文件夹；从 V08 复制 `server.py / start_server.bat` 并改字段校验；手写 `state.json`；`launch.json` 加一项 | 服务起得来，POST 非法字段被拒 | 无 |
| 1 | Rhino：新建 `massing.3dm`，`Handles / Preview` 图层，一个手柄点 | 文件能开，点在图层上 | Rhino 开着 |
| 2 | GH：读 json → 周界 → 三层楼板预览；写回 `results.floors` | 手改 json 的 `depth`，Rhino 里三层凹口同步变（≤ 1 s） | Grasshopper 开着 |
| 3 | GH：手柄 → `pos / depth` 写回；`ops` 更新 → 手柄跟着移 | 拖点，json 变，楼板变；改 json，点移动 | 你在 Rhino 里拖一次 |
| 4 | GH：立面分段 + 带窗预览；写回 `results.segments` | 凹口后段数 4 → 7，每段朝向正确（手算对照） | 看一眼 Rhino |
| 5 | 网页：三组滑块、同步、段表（引擎）、模板解读、手柄回流、自检 | 改滑块 → Rhino 变 → 表变；拖点 → 滑块变 | 浏览器里试 |
| 6 | 边界、截图、WORK_LOG、提交 | 全过 | 看结果 |
| 7 | Ladybug：EPW（随页面气候选择）+ 分析期（夏 / 冬 / 全年）+ SunPath → **Direct Sun Hours**（分析面 = 窗条网格，context = 楼板）→ 按段写回 `results.sun` | 换分析期，北向冬季 0 h；凹口两侧段低于同向的直段 | 无 |
| 8 | 页面：段表加「直射日照」列，解读加一句；分析期下拉 | 切换分析期 ≤ 10 s 刷新 | 浏览器里试 |

**第 4 步之前不碰网页**。

**第 7 步的一处替换（2026-10-02）**：计划写的是入射辐射，但 Ladybug 的天空矩阵需要 Radiance，这台电脑没装，所以第一刀的 Ladybug 指标改为「直射日照小时」（纯几何，不需要 Radiance，也不含云）。装好 Radiance 后把 `LB Cumulative Sky Matrix + LB Incident Radiation` 接回同一条链即可，写回脚本只需多一个字段。

---

## 7. 验收

| 项 | 通过标准 |
|---|---|
| 环路 | 网页滑块 → Rhino ≤ 1 s；Rhino 手柄 → 网页滑块 ≤ 2 s；段表随之刷新 |
| 几何 | 凹口三层同形；段数与朝向正确；窗面积 = 段长 × 窗高 |
| 物理方向 | 凹口开在南边时，新增的东西向段过热高于原南段的北侧对应段；凹口深度加大，整栋采光系数升（立面更长） |
| 状态 | 关掉网页再开，参数从 json 恢复；Rhino 重开后手柄位置保留 |
| 不受影响 | Strip Window 页面与共享引擎自检不变（引擎不改） |

---

## 8. 第二刀及以后（只列）

1. ~~机构库条目移植到 GH：先做竖轴膝盖折板；装置沿每一段墙排布；网页的装置参数卡原样复用；翻译规则不变。~~ **已做（2026-10-02）**：`shading` 参数卡进 json；GH 生成单元面片（每层每段，中间排满、固定边交替）并作为日照 context；每段写回 `dev = {screen, screenDay, view, units}`；页面装置分组 + 无板 / 有板两列 + 视野列。其余条目（中轴转动板、横轴折板、伞式六角）待移植。
2. Ladybug 装好后：窗面入射辐射作为第二口径，热力图在 Rhino，数字并排在段表。
3. 操作词汇：~~庭院~~ **庭院已做（2026-10-02）**：`ops` 里第二条 `{type:'court', pos_u, pos_v, width, depth}`，中心手柄 `court01`（蓝点）；周界 = 外圈 + 内圈（顺时针，墙朝天井），内墙段 Y1–Y4；楼板实体带洞（Extrusion 内轮廓只能在 z=0 做一次再逐层平移）；庭院离外墙 ≥ 1 m、与凹口挨着时忽略并写警告。U 形、移边；楼层组；父子比例 待做。
4. 平面热力图：网格改为"每格找最近墙段"，接回引擎的网格条件。
5. Claude 读图填卡接到网页；解读由模板换成模型。

---

## 9. 已定与待定

- 已定：遮阳第一刀不做；指标用共享引擎；凹口默认在 A 边（朝南）。
- 待定：Ladybug 版本（装好后告诉我）；凹口深度上限（建议 ≤ 短边一半）；手柄点是否同时控制宽度（建议不，宽度只在网页改）。
