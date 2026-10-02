# i18n_en.py — build the English-interface copy of the MassShadeLight page (2026-10-02)
# Source of truth is massing-tool.html (Chinese). Run this after editing it:
#     python i18n_en.py
# It writes massing-tool-en.html next to it. Chinese-only code comments are dropped; every other
# Chinese fragment is replaced through the table below (longest first). The script fails loudly if any
# Chinese is left, so a new string in the page = one more line in MAP.
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "massing-tool.html")
OUT = os.path.join(HERE, "massing-tool-en.html")

MAP = {
# ---- header / tabs
"MassShadeLight · 体量与立面": "MassShadeLight · massing & facade",
"体量 × 立面遮阳 × 室内过热与采光": "massing × facade shading × overheating & daylight",
"设计": "Design", "对比": "Compare", "读图": "Read image",
"方案名（可空）": "scheme name (optional)", "存为方案": "Save scheme",
"已连接本地服务": "connected to local service", "未连接本地服务（双击": "no local service (double-click", "未连接本地服务": "no local service",
"在「设计」里调好后点「存为方案」。右边勾选 2–4 个方案并排看。方案保存在这台电脑的浏览器里，换电脑请用导出 / 导入。": "Tune a scheme in Design, then click Save scheme. Tick 2–4 schemes on the right to see them side by side. Schemes live in this browser; use export / import to move them.",
"四种装置各跑一遍": "Run all four devices", "连日照一起跑（每种约 30 秒）": "include sun hours (about 30 s each)", "以当前设计为底，跑五个方案": "Uses the current design as the base and saves five schemes",
"读图：从一张装置的图到参数卡": "Read image: from a picture of a device to a parameter card",
"右边上传装置的运动分析图或照片，写一句描述，发送。": "Upload a motion diagram or photo of a device on the right, add one line of description, send.",
"卡出来后每一格都能改。": "Every field of the card can be edited once it appears.",
"「应用到设计」直接换成这个装置；「存入机构库」交给": "Apply to design swaps the device in; Add to library hands it to",
"整理成条目。": "to write up as a library entry.",
"模式：": "mode: ", "。没有": ". Without an", "时，上传后在聊天里对": ", upload and then tell", "说「读图」。": "“read image” in the chat.",
"库里没有的运动方式，卡会说最接近哪个条目、差在哪；要做成三维需要": "For a motion the library lacks, the card names the closest entry and the difference; building it in 3D needs",
"加新条目。": "to add a new entry.",
# ---- building
"建筑": "Building", "基底与楼层": "Footprint & floors", "长": "Length", "层数": "Floors", "层高": "Height", "楼板厚": "Slab", "边朝向": "faces",
"、C 边长 L，B、D 边长 W。A 边朝向": " and C are L long, B and D are W long. A facing", "° = 朝南，四条边按 A、B、C、D 顺时针排。": "° = south; the four edges run A, B, C, D clockwise.",
"楼层组": "Floor groups",
"楼层从下往上分组，最后一组自动拿剩下的楼层。每组可以四边退台，也可以整组错位。点 + 加一组，删 删掉当前组。": "Floors are grouped from the bottom up; the last group takes whatever is left. Each group can set back on four sides or shift as a whole. + adds a group, Del removes the current one.",
"本组层数（其余楼层）": "Floors in group (the rest)", "本组层数": "Floors in group", "边退台": "setback", "错位 沿": "Shift along", "（空）": " (empty)",
"窗墙比": "Window-wall ratio", "窗台高": "Sill height", "窗": "Windows", "每段墙一条通长的窗带，高度由窗墙比算出。": "One continuous window band per wall segment; its height follows the window-wall ratio.",
# ---- environment
"环境与计算": "Environment & calculation", "房间进深": "Room depth", "离窗多远以内算作": "How far from the window counts as the", "靠窗的房间带": "window-side room band",
"。过热和采光都按这条带算，更深的地方不计。": ". Overheating and daylight are evaluated in this band; deeper floor area is not counted.",
"气候": "Climate", "当下（机场站）": "Today (airport)", "当下（港口站）": "Today (harbour)", "年预测": " projection",
"热质量": "Thermal mass", "轻": "light", "中": "medium", "重": "heavy",
"开窗通风": "Window ventilation", "不开窗": "closed", "开窗（约 2 次/h）": "open (≈2 ach)", "穿堂风（约 4 次/h）": "cross-vent (≈4 ach)",
"日照分析期": "Sun period", "夏季 6–8 月": "Summer Jun–Aug", "冬季 12–2 月": "Winter Dec–Feb", "全年": "Annual", "夏季": "Summer", "冬季": "Winter",
"计算": "Calculate", "关掉后拖滑块更快；日照和受晒两列停在上一次的值。": "Off = sliders respond faster; the sun-hours and exposure columns keep their last values.",
# ---- topology
"拓扑操作": "Topology operations",
"三种操作都可以有多个：点 + 新增，点 删 删掉当前这个。Rhino 里的彩色点是手柄（红 凹口、蓝 庭院、绿 分裂），拖它和拖滑块一样，谁后动谁算数。": "Each operation can be repeated: + adds one, Del removes the current one. The coloured points in Rhino are handles (red notch, blue courtyard, green split); dragging one is the same as moving a slider, the later move wins.",
"凹口": "Notch", "来自": "from", "在哪条边": "Edge", "作用在": "Applies to", "全部楼层": "all floors", "位置（沿边）": "Position (along edge)",
"深过一半就是 U 形，最深到对面墙前 1 m。两个凹口挨得太近（1 m 以内）时后加的会被忽略。": "Deeper than half makes a U; the deepest stops 1 m before the far wall. Two notches closer than 1 m: the later one is ignored.",
"庭院": "Courtyard", "中心 沿": "Centre along", "宽（沿 L）": "Width (along L)", "深（沿 W)": "Depth (along W)", "深（沿 W）": "Depth (along W)",
"庭院四面内墙朝内开窗。庭院离外墙至少 1 m，不能和凹口或别的庭院挨着，挨着的会被忽略。只开在下面几组时，上面的楼层会把它盖住。": "The four inner walls of a courtyard get windows facing in. Keep it 1 m from the outer wall and clear of notches and other courtyards, or it is ignored. Opened only in lower groups, the floors above cover it.",
"分裂": "Split", "切的方向": "Cut direction", "横着切，分成左右两块": "across: left / right halves", "竖着切，分成前后两块": "along: front / back halves", "切线位置": "Cut position", "缝宽": "Gap",
"把楼板切成两块、中间留缝。缝两侧的墙也是立面（S1、S2），一样开窗装装置。切线穿过凹口或庭院、或一边不到 2 m 时不切。": "Cuts the slab in two with a gap between. The walls along the gap are facades too (S1, S2) with windows and devices. No cut if the line crosses a notch or courtyard, or leaves a side under 2 m.",
# ---- devices
"遮阳装置": "Shading device", "装置": "Device", "无装置": "none", "中轴转动板": "pivot panel", "膝盖式折板 · 竖轴": "knee fold · vertical axis", "膝盖式折板 · 横轴": "knee fold · horizontal axis", "伞式六角折板": "hexagonal umbrella",
"竖轴折板": "vertical fold", "横轴折板": "horizontal fold", "伞式六角": "hex umbrella",
"从第几层起装": "Install from floor", "层起": "up", "开合": "Opening",
"这是总闸：拖它，下面每个立面一起动；单独拖某一面只改那一面。不勾 = 这一面不装。": "Master control: drag it and every facade below follows; drag one facade to change only that one. Unticked = no device on that facade.",
"庭院内墙": "Courtyard walls", "凹口里的墙跟着它所在的边；分裂的缝两侧按默认折角。": "Walls inside a notch follow their edge; the two sides of a split gap use the default angle.",
"单元与排布": "Unit & layout", "单元宽度": "Unit width", "每组几片": "Panels per group", "排满，不分组": "fill, no groups", "每组 1 片": "1 per group", "每组 2 片": "2 per group", "每组 3 片": "3 per group", "随机": "random",
"固定边（不适用）": "Fixed edge (n/a)", "固定边": "Fixed edge", "逐片交替": "alternate", "同向": "same side", "片间隔": "Panel gap", "组间隔": "Group gap", "片": " panels",
"沿每段墙从中间排起，能放几组放几组。分了组，两个间隔才起作用。灰掉的 = 这种装置用不到。": "Laid out from the middle of each wall, as many groups as fit. The two gaps only matter once panels are grouped. Greyed = not used by this device.",
"板厚（不用）": "Thickness (unused)", "板厚": "Thickness", "这种装置按面状投影算，板厚不影响结果": "This device is evaluated as a projected screen; thickness has no effect", "这种装置的固定边是定死的": "The fixed edge of this device cannot change",
"倾角（0 平行立面 · 90 垂直）": "Tilt (0 parallel to facade · 90 perpendicular)", "倾角（0 贴平 · 90 垂直）": "Tilt (0 flat · 90 perpendicular)", "单片宽": "Panel width", "倾角方向": "Tilt direction",
"一片板绕自己的竖向中轴转动。倾角越大，板越侧过去，挡得越少、看出去越通透。": "One panel turns about its own vertical axis. The larger the tilt, the more it turns away: less shading, more view.",
"折角（0 贴平 · 90 全折）": "Fold (0 flat · 90 fully folded)", "单元宽（贴平时）": "Unit width (flat)",
"两片竖板像书脊朝外的书：一边固定，另一边沿导轨滑过来，折线向外凸。折得越开，占的立面越短、露出的窗越多。": "Two vertical leaves like a book with its spine outward: one edge fixed, the other slides along a rail, the fold bulges out. The more it folds, the shorter the facade it covers and the more window shows.",
"板宽（一开间）": "Panel width (one bay)",
"一块一层高的板横着折：顶边固定，底边往上滑，膝盖向外凸。折起来露出窗的下部，凸出的膝盖像一道挑檐挡高角度的太阳。": "A floor-high panel folds across: top edge fixed, bottom edge slides up, the knee bulges out. Folding exposes the lower window; the knee works like an overhang against high sun.",
"折角（0 全闭 · 90 全开）": "Fold (0 closed · 90 fully open)", "单元宽（平边距）": "Unit width (across flats)",
"六角形的伞：六个角固定，中间的推杆把六片网布顶起来。折角越大，伞收得越紧，盖住的面积越小。": "A hexagonal umbrella: six corners fixed, a central rod pushes six mesh leaves out. The larger the fold, the tighter the umbrella and the smaller the covered area.",
"不装遮阳装置。": "No shading device.", "不装遮阳装置": "No shading device", "不装": "no device",
"新增": "Add", "删掉当前这条": "Delete the current one", "删": "Del",
# ---- Rhino status
"状态": "status", "最近写回": "Last write-back", "立面段数": "Facade segments", "各层面积": "Floor areas", "窗高": "Window height",
"滑块一动就自动同步到 Rhino，重算后页面自己更新；这里只是看一眼状态。": "Sliders sync to Rhino automatically and the page refreshes after each recompute; this is just a status readout.",
# ---- plan card
"平面": "Plan", "过热暴露": "Overheating exposure", "采光": "Daylight", "只看立面段": "segments only", "格": "cell", "标准层平面与立面段": "Typical floor plan with facade segments",
"北朝上。外圈是罗盘；两道弧是太阳方位：橙色冬至、红色夏至，弧的两端是日出和日落方向，鼠标停上去看角度。底色是每一格的过热暴露或采光，从面向它的墙段按距离摊开；灰格离所有外墙都太远，立面管不到。彩色点是": "North is up. The outer ring is a compass; the two arcs are sun azimuths, orange winter solstice and red summer solstice, their ends are sunrise and sunset, hover for angles. Cell colour is overheating exposure or daylight, spread from the wall segments facing it by distance; grey cells are too far from every outer wall for the facade to matter. Coloured dots are",
"里的手柄。": "handles.",
# ---- data card
"立面段": "Facade segments", "段": "Seg", "朝向": "Facing", "长度": "Length", "视野": "View", "过热 无板": "Overheat bare", "有板）": "with device)", "有板": "with", "采光 无板": "Daylight bare", "受晒": "Exposure", "日照": "Sun",
"等待": "waiting for", "写回立面段": "to write back the segments…",
"整栋过热（无板": "Whole building overheating (bare", "整栋采光（无板": "Whole building daylight (bare", "整栋过热（无凹口": "Whole building overheating (no notch", "整栋采光（无凹口": "Whole building daylight (no notch", "有凹口，均无板）": "with notch, both bare)", "冬季净得热（无板": "Winter net gain (bare",
"过热 = 全年室内高于": "Overheating = share of hours above", "°C 的小时占比，被动房要求不超过 10 %，建议 5 % 以内。采光 = 房间带平均采光系数，3 % 算充足。两列「无板 / 有板」= 不装 / 装遮阳装置。受晒 = 这段墙被自己的体量挡掉后还能晒到的比例。日照": "°C indoors over the year; Passive House allows at most 10 %, 5 % is recommended. Daylight = mean daylight factor of the room band, 3 % counts as sufficient. “bare / with” = without / with the shading device. Exposure = how much direct sun this segment still gets after the building massing itself blocks part of it. Sun =",
"算的直射小时数。过热和采光是估算，适合比大小，不适合当绝对值。": "direct sun hours from Ladybug. Overheating and daylight are estimates: good for comparing, not for absolute values.",
# ---- section card
"剖面": "Section", "所选立面段的窗洞剖面：窗台、窗头、遮阳装置与太阳角": "Window section of the chosen segment: sill, head, shading device and sun angles",
"切在遮阳装置上：自动取装了装置、过热最高的那段外墙（没装置时画窗洞本身）。外面在左，房间在右。黑色粗线是遮阳装置的侧影。红色是高温时段的直射光，橙色是冬季直射光，角度是这个朝向在那段时间里的直射加权平均剖面角（气象数据）；两条细虚线是夏至、冬至正午的实际太阳角（按气候站纬度）。光线被装置挡掉的部分不画；穿过板缝的用淡色画。": "Cut through the shading device: the outer wall with a device and the highest overheating is picked automatically (just the window if there is no device). Outside on the left, room on the right. The thick black line is the device profile. Red is direct sun in hot hours, orange is winter direct sun; the angles are the direct-weighted mean profile angles for this orientation (climate data). The two thin dashed lines are the real solstice-noon sun angles (station latitude). Light blocked by the device is not drawn; light through gaps is drawn faint.",
"等待数据。": "Waiting for data.",
# ---- interpret / compare / read cards
"解读": "Reading", "方案列表": "Schemes", "勾 2–4 个并排看。点名字改名，点「删」两次删掉。": "Tick 2–4 to compare. Click a name to rename, click Del twice to delete.", "导出全部": "Export all", "导入": "Import",
"方案对比": "Scheme comparison", "在左边勾选方案。": "Tick schemes on the left.",
"读图 · 新装置": "Read image · new device", "图（可多张，最多 6）": "Images (up to 6)", "一句描述（可空，比如": "One line (optional, e.g.", "两片板，底边固定，膝盖向外": "two leaves, bottom fixed, knee outward", "发送": "Send",
# ---- JS: layout / warnings
"和前一个庭院挨太近": "too close to an earlier courtyard", "碰到凹口": "hits a notch", "放不下": "does not fit", "重叠": "overlaps", "和": "overlaps #", "共": "in", "组（": "groups (",
"忽略了它（两个凹口之间至少留 1 m 墙）。换条边、挪位置或改小就会出现。": "ignores it (keep at least 1 m of wall between notches). Change the edge, move it or shrink it and it will appear.",
"忽略了它（庭院离凹口、外墙和其他庭院至少 1 m）。": "ignores it (a courtyard needs 1 m from notches, outer walls and other courtyards).",
"这些楼层上": "on these floors", "横切": "across", "竖切": "along", "缝": "gap", "组退台）": "set back)", "组错位）": "shifted)", "· 窗墙比": "· WWR", "· 进深": "· depth", "无操作": "none", "组": "groups", "层 ·": "floors ·",
"已写入": "written to", "，等待": ", waiting for", "写入失败：": "write failed: ", "已写回": "wrote back at", "秒没回写：": " s without a write-back: ", "里的": " ", "可能停了，点它一下暂停再点播放（或重新打开": "may have stopped: click it to pause then play (or reopen",
"段（": " segments (", "层）": " floors)", "引擎未加载": "engine not loaded", "（第": " (group", "组）": ")", "日照 h（": "Sun h (", "计算中": "computing", "待日照": "needs sun", "整栋过热": "Whole-building overheating", "整栋": "Total",
# ---- section JS
"横轴折板：挂在上层楼板下，折角": "Horizontal fold: hung from the slab above, fold", "°，膝点挑出": "°, knee projects", "，板脚落到": ", foot ends at", "高（窗头": " height (head at",
"竖向旋转板：离墙": "Vertical pivot panel: standoff", "，转": ", turned", "°，侧影伸出": "°, profile reaches", "竖向折板：离墙": "Vertical fold: standoff", "，折角": ", fold", "°，折缝伸出": "°, fold line reaches",
"伞状单元：对着窗中心，离墙": "Umbrella unit: centred on the window, standoff", "，开": ", opened", "°，尖点伸出": "°, tip reaches", "；单元之间透过": "; between units", "% 直射": "% of direct sun passes",
"挑出": "projects", "旋转板侧影": "pivot panel profile", "折板侧影": "fold profile", "伸出": "reach", "°：被装置完全挡住": "°: fully blocked by the device", "（透过": " (passes", "照到内墙": "reaches the back wall", "照入": "reaches", "高温时段": "Hot hours", "冬季这面几乎没有直射光": "almost no winter direct sun on this facade",
"转": "Turned", "° 时板的内半边伸进墙": "°, the inner half of the panel runs into the wall by", "：离墙距离不够或板太宽": ": standoff too small or panel too wide",
"这是一个单元的剖面：沿墙只有": "Section of one unit: only", "% 被单元盖住，其余窗面照常进光": "% of the wall is covered, the rest of the window gets sun as usual",
"夏至正午": "Summer-solstice noon", "冬至正午": "Winter-solstice noon", "晒不到这面": " does not reach this facade", "：太阳在这面墙背后": ": sun is behind this wall", "°（细虚线，实际太阳）": "° (thin dashed, real sun)",
"窗台": "sill", "窗头": "head", "进深": "depth", "（只画到 6 m）": " (drawn to 6 m)", "外": "out", "内": "in", "° ·": "° ·",
"装置后高温时段的太阳得热剩": "With the device, hot-hour solar gain is", "%，冬季得热剩": "%, winter gain", "%（都相对不装）。": "% (both relative to no device). ",
"直射：窗面": "direct sun: window", "，只有楼板遮挡时": ", slabs only", "，受晒": ", exposure", "日照还没算完。": "sun hours not finished yet.", "（纬度": " (latitude", "°）。": "°).",
# ---- plan JS
"北": "N", "东": "E", "南": "S", "西": "W", "夏至：太阳从": "Summer solstice: sun rises at", "冬至：太阳从": "Winter solstice: sun rises at", "° 升起、": "°, sets at ", "° 落下": "°", "冬至": "winter", "夏至": "summer",
"（主要来自": " (mostly from", "，离墙": ", distance", "离所有外墙都超过": "more than", "，不在房间带内": " from every outer wall, outside the room band", "段 ·": "segments ·", "· 过热暴露最高": "· max overheating exposure", "· 采光最高": "· max daylight", "% 面积在房间带外": "% of area outside the room band",
# ---- interpret JS
"楼层分": "Floors in", "组：": " groups: ", "退": "set back", "错位": "shift", "；各层面积": "; floor areas", "，只作用于第": ", only group", "边（": " edge (", "）深": ") depth", "、宽": ", width", "（深过一半，已是 U 形）": " (deeper than half: a U)",
"边被切成": " edge is cut into", "有凹口因为挨得太近被忽略（见": "A notch too close to another was ignored (see", "警告）。": "warnings).", "当前没有凹口。": "No notches.",
"分裂：": "Split: ", "横着": "across", "竖着": "along", "% 处切开，缝": "%, gap", "第 1 层分成两块（": "floor 1 splits into two plates (", "），缝两侧的新立面是": "); the new facades along the gap are", "本层没有生效": "not effective on this floor",
"；有楼层的分裂被忽略（切线穿过凹口 / 庭院，或一边太窄，见警告）": "; on some floors the split is ignored (line crosses a notch / courtyard, or a side is too thin, see warnings)",
"；本层生效": "; effective on this floor:", "个": "", "（其余太小、太靠外墙，或与凹口 / 其他庭院挨着，被忽略，见警告）": " (the rest are too small, too close to the outer wall, or touch a notch / other courtyard, see warnings)", "；内墙里过热最高的是": "; hottest inner wall is",
"过热最高的是": "Hottest segment:", "）：": "): ", "%；采光最好的是": "%; best daylight:", "和不开凹口的矩形相比（都不装遮阳），整栋过热": "Compared with the plain rectangle (both without devices), whole-building overheating", "上升": "rises", "下降": "falls", "个百分点，采光": "points, daylight", "个百分点；立面总长（各层合计）从": "points; total facade length (all floors) goes from", "个百分点": "points", "变为": "to",
"装上": "With ", "；共": "; ", "个单元）后，整栋过热从": " units), whole-building overheating goes from", "%，采光从": "%, daylight from", "%，视野通透": "%, view openness", "%；仍最热的是": "%; still hottest:", "%）。": "%).",
"直射日照（": "direct sun (", "）：最多的是": "): most on", "），最少的是": "), least on", "；凹口内的": "; inside the notch,", "被凹口两侧的楼板遮住了一部分": "are partly shaded by the slabs on both sides",
"平面热力图（": "Plan heatmap (", "，格": ", cell", "，房间带进深": ", room band depth", "）：过热暴露最高的一块在": "): highest overheating exposure at", "），最低的在": "), lowest at", "；有": "; ", "% 的楼板离所有外墙都超过": "% of the slab is more than", "，不在任何房间带里，立面对它没有影响，这块面积要靠人工照明": " from every outer wall, outside any room band: the facade cannot help it and it needs artificial light",
"都不装遮阳：自由墙面 vs 算进自遮挡": "both without devices: free wall vs with self-shading", "体量自遮挡：": "Self-shading: ", "段墙被自己的体量挡住了一部分太阳": "segments lose part of their sun to the building massing itself", "，对过热影响最大的是": "; the biggest effect on overheating is", "（受晒": " (exposure", "%，过热": "%, overheating", "，但这些段本来就不热，过热几乎没变": ", but these segments were not hot anyway, overheating barely changes",
"；庭院四壁受晒 0 %，因为庭院只开在第 1 组，上面的楼层把它盖住了，直射完全进不来": "; the courtyard walls have 0 % exposure because the courtyard is only open in group 1 and the floors above cover it, no direct sun gets in",
"。不装遮阳时，算进自遮挡整栋过热从": ". Without devices, counting self-shading moves whole-building overheating from", "体量自遮挡：所有墙段受晒都在 90 % 以上，这个体量基本不遮自己。": "Self-shading: every segment keeps over 90 % exposure; this massing barely shades itself.", "体量自遮挡待": "Self-shading will be counted after", "第二次日照算完后才计入（表里「受晒」列）。": "finishes the second sun run (the Exposure column).",
# ---- snapshots / compare JS
"还没有结果，等": "No results yet; wait for", "写回后再存。": "to write back before saving.", "方案": "Scheme", "已存「": "saved “", "」（共": "” (", "个方案）": " schemes)", "个 · 选了": " · selected", "还没有方案。回到「设计」调好后点「存为方案」。": "No schemes yet. Go back to Design, tune, then click Save scheme.", "并排看": "compare", "（点击改名）": " (click to rename)", "再点一次确认": "click again to confirm", "确认删": "Confirm", "导入了": "imported", "个方案": " schemes", "导入失败：": "import failed: ",
"整栋过热 · 无板": "Overheating · bare", "整栋过热 · 有板": "Overheating · with device", "整栋采光 · 无板": "Daylight · bare", "整栋采光 · 有板": "Daylight · with device", "视野通透": "View openness", "受晒（自遮挡后）": "Exposure (after self-shading)", "日照 h（分析期）": "Sun h (period)", "楼板总面积": "Total floor area", "立面总长（各层合计）": "Total facade length (all floors)", "装置单元数": "Device units", "冬季净得热": "Winter net gain",
"个方案，差值相对第一个（": " schemes; differences relative to the first (", "在左边的方案列表里勾选 2–4 个。": "Tick 2–4 schemes in the list on the left.", "装置 · 折角": "Device · fold", "体量 · 操作": "Massing · operations", "立面段差异（有板；只列过热差": "Segment differences (with device; only segments with overheating diff", "或采光差": "or daylight diff", "的段，最多 30 行）": ", at most 30 rows)", "各段都没有明显差别。": "No segment differs noticeably.", "过热 · 采光 · 视野": "overheating · daylight · view", "（无此段）": " (no such segment)", "持平": "same", "高": "higher", "低": "lower", "「": "“", "」比「": "” vs “", "」：": "”: ", "过热（有板）": "overheating (with device)", "采光（有板）": "daylight (with device)", "立面总长": "facade length", "楼板面积": "floor area", "；段里差别最大的是": "; the largest segment difference is", "（过热": " (overheating",
"还没有结果。": "No results yet.", "正在跑：": "running: ", "超时，跳过": "timed out, skipped", "装置 ·": "device ·", "跑完，存了": "done, saved", "个方案；装置已恢复为": " schemes; device restored to",
# ---- inbox JS
"挡哪个方向的太阳": "Which sun direction it blocks", "元素的方向": "Element direction", "单元尺寸（宽 / 深 / 厚）": "Unit size (width / depth / thickness)", "单元密度与排布": "Unit density & layout", "透不透（穿孔率）": "Transparency (perforation)", "动不动（怎么动）": "Movement (how it moves)", "在玻璃哪一侧": "Which side of the glass", "盖住窗的哪部分": "Which part of the window it covers",
"先选图。": "Choose images first.", "已发送，模型在读（": "sent, the model is reading (", "正在存入收件夹": "saving to inbox", "读好了，看下面的卡。": "done, see the card below.", "已存入收件夹。现在在聊天里对": "saved to the inbox. Now tell", "说「读图」，卡出来会自动显示在下面。": "“read image” in the chat; the card will appear below.", "发送失败：": "send failed: ",
"直接调模型": "call the model directly", "（没有": " (no", "收件夹是空的。": "The inbox is empty.", "等读": "unread", "已有卡": "card ready", "已应用": "applied", "已标记入库": "marked for library", "待": "pending", "（无描述）": " (no description)", "还没有卡。": "No card yet.", "调模型读": "Read with the model", "读：在聊天里说「读图」。卡写进收件夹后这里会自动显示。": "to read: say “read image” in the chat. The card shows here once it is in the inbox.",
"参数卡（每格都能改）· 来源": "Parameter card (every field editable) · source", "· 把握": "· confidence", "怎么动": "How it moves", "最接近的条目": "Closest entry", "都不像（要加新条目）": "none (needs a new entry)", "不同之处": "Differences", "依据": "Evidence", "提醒": "Notes", "进工具的参数（和装置卡同名）": "Tool parameters (same names as the device card)", "单元宽": "Unit width", "代表折角": "Typical fold", "表皮厚": "Skin thickness", "孔径": "Hole size", "穿孔率下限": "Perforation min", "穿孔率上限": "Perforation max", "折角范围": "Fold range",
"保存修改": "Save edits", "应用到设计": "Apply to design", "存入机构库": "Add to library", "重新读": "Read again", "模型在读": "model reading", "这张卡没有对应的条目，先在「最接近的条目」里选一个。": "This card has no matching entry; pick one under Closest entry first.", "已按「": "applied as “", "」应用，等": "”, waiting for", "重算": "to recompute", "已标记入库：在聊天里让": "marked for the library: in the chat, ask", "整理进": "to write it into", "已标记：在聊天里让": "marked: in the chat, ask", "加新条目": "to add a new entry", "卡已保存": "card saved", "读图操作失败：": "read-image action failed: ",
# ---- misc short
"模板句，数字全部来自引擎与": "Template sentences; every number comes from the engine and", "；以后由模型改写成设计语言。": "; later a model will rewrite them in design language.",
"板与板之间透过": "between panels", "离墙 m": "Standoff m", "离墙": "standoff",
"交给": "hand to", "加条目": "add entry", "等": "wait", "在": "at", "第": "group", "空": "empty", "深": "depth", "宽": "width", "庭": "court", "边后": "edge)", "·": "·", "｜": "|",
"% 到": "% to", "% ·": "% ·", "%。": "%.", "%）": "%)", "个：": ":", "层": "floors", "、": ", ", "；": "; ", "，": ", ", "。": ". ", "：": ": ", "（": " (", "）": ")", "°": "°", "％": "%",
}

LINE = {   # exact source templates → English, applied before MAP (word order)
"第 ${i+1} 组 ${g.floors": "group ${i+1} ${g.floors",
"第 ${i+1} 组（${r.n ? `F${r.fro": "group ${i+1} (${r.n ? `F${r.fro",
"楼层分 ${GL.length} 组：": "Floors in ${GL.length} groups: ",
"只作用于第 ${a.slice(1)} 组": "only group ${a.slice(1)}",
"凹口 ${notchOps.length} 个：": "Notches (${notchOps.length}): ",
"庭院 ${courtOps.length} 个：": "Courtyards (${courtOps.length}): ",
"在 ${op.edge} 边（${dirOf(op.edge)}）深": "on edge ${op.edge} (${dirOf(op.edge)}), depth",
"${e} 边被切成": "edge ${e} is cut into",
"；本层生效 ${loops.length} 个": "; ${loops.length} effective on this floor",
"；共 ${nU} 个单元）后，整栋过热从": "; ${nU} units), whole-building overheating goes from",
"}直射：窗面": "} direct sun: window",
"· ${P.devFrom} 层起": "· from floor ${P.devFrom}",
"`组 ${i+1}": "`Group ${i+1}",
"F${f.i}（第 ${f.group} 组）": "F${f.i} (group ${f.group})",
"' 边后 '+fmt(hot.topD,1)+' m'": "' edge, '+fmt(hot.topD,1)+' m in'",
"' 边后 '+fmt(cool.topD,1)+' m'": "' edge, '+fmt(cool.topD,1)+' m in'",
"'（主要来自 '+c.top.edge+'，离墙 '+fmt(c.topD,1)+' m）'": "' (mostly from '+c.top.edge+', '+fmt(c.topD,1)+' m in)'",
}

def strip_cjk_comments(line):
    """Drop a trailing // comment that contains Chinese (code comments are not part of the interface)."""
    if not re.search(r"[一-鿿]", line):
        return line
    idx = line.rfind(" //")
    while idx > 0:
        head = line[:idx]
        if all(head.count(q) % 2 == 0 for q in ("'", '"', "`")) and re.search(r"[一-鿿]", line[idx:]):
            return head.rstrip()
        idx = line.rfind(" //", 0, idx)
    return line

def build():
    s = io.open(SRC, encoding="utf-8").read()
    s = "\n".join(strip_cjk_comments(l) for l in s.split("\n"))
    s = s.replace('<html lang="zh">', '<html lang="en">')
    for zh, en in LINE.items():
        assert s.count(zh) == 1, ("LINE anchor missing or duplicated: " + zh)
        s = s.replace(zh, en)
    for zh in sorted(MAP, key=len, reverse=True):
        s = s.replace(zh, MAP[zh])
    # directions come from the shared engine (Chinese): swap the list and the lookup on the page side
    s = s.replace("const ENGINE = (typeof window.WWR!=='undefined') ? window.WWR : null;",
                  "const ENGINE = (typeof window.WWR!=='undefined') ? window.WWR : null;" + chr(10) +
                  "  if(ENGINE){ ENGINE.DIRS = ['N','NE','E','SE','S','SW','W','NW']; ENGINE.dirName = az => ENGINE.DIRS[Math.round(ENGINE.norm(az)/45)%8]; }")
    s = s.replace('href="massing-tool-en.html">EN</a>', 'href="massing-tool.html">&#20013;&#25991;</a>')   # 中文 link, written as escapes so the leftover check stays clean
    s = re.sub(r"[ \t]+\n", "\n", s)
    left = sorted(set(re.findall(r"[^\n]{0,30}[　-〿一-鿿＀-￯][^\n]{0,30}", s)))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(s)
    if left:
        print("UNTRANSLATED (%d):" % len(left)); print("\n".join(left[:60])); sys.exit(1)
    print("wrote", OUT, "(%d chars)" % len(s))

if __name__ == "__main__":
    build()
