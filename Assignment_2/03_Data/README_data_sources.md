# 数据来源（03_Data）

| 文件 | 内容 | 来源 | 许可 | 下载日期 |
|---|---|---|---|---|
| `CityOfVancouver_local-area-boundary.geojson` | 温哥华 22 个社区（local area / local planning area）的边界，WGS84 经纬度 | City of Vancouver Open Data Portal，数据集 *Local area boundary*（opendata.vancouver.ca，最后修改 2023-06-24；平台说明：边界不再变动，大致沿街道中线） | Open Government Licence – Vancouver（使用时注明出处） | 2026-10-18 |

工具 `02_Prototypes/Version_01/index.html` 里嵌入的是由这个文件换算的版本：经纬度换算成以北纬 49.25°、西经 123.12° 为原点的近似米坐标（等距圆柱近似，整个城市范围内误差很小，只用于画地图和量面积），坐标取整到 1 m。

以后可能用到（已在平台上确认存在，尚未下载）：Property parcel polygons（地块，2026-10-12 更新）、Building footprints 2009（建筑轮廓和离地高度，来自 2009 年激光扫描，偏旧）、Zoning districts and labels（分区规划代号）。

## 工具运行时联网查询的数据（2026-10-18 起，第 3 步选场地时）
不下载到项目里；选社区时由网页直接向 opendata.vancouver.ca 查询（Opendatasoft API，允许网页跨域访问）：
- *Parks – polygon representation*：按社区名（local_area）查询这个社区的公园边界。
- *Property parcel polygons*：按社区外接框查询地块，再只留中心点在社区边界内的。
- *Community centres*：按社区名查询已有社区中心的位置。
许可均为 Open Government Licence – Vancouver。

## 选场地后联网查询的数据（2026-10-18 起）
按“用这个场地”后查询，范围是场地外接框外扩 200 m；结果只存在网页里，不下载到项目：
- *Building footprints 2009*：建筑轮廓和离地高度（`hgt_agl`），2009 年激光扫描，偏旧。第 4–6 步三维里的周边建筑。
- *Public streets*：道路中心线（`hblock` 街区名、`streetuse` 用途）。第 6 步的道路。
- *Right-of-way widths*：道路红线宽度（点数据，`width`，米）。第 6 步道路的宽度。
- *Public trees*：公共树木（`common_name` 树种、`height_m` 高度、`diameter_cm` 胸径），包括街道树和公园树。第 6 步的树木；树冠大小是示意，数据里没有冠幅。
许可均为 Open Government Licence – Vancouver。

## 气象数据（2026-10-19 起，太阳辐射分析）
- 工具里嵌入的 `WEATHER`（逐小时 DNI、DHI，Wh/m²）来自项目里已有的 `Passivehouse_Tool/02_Data/EPW/CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw`（温哥华国际机场，CWEC2020，Environment Canada；2026-09-24 从 Climate.OneBuilding.Org 下载，来源说明见那个文件夹的 README）。没有重新下载。
- 转换（脚本 `03_Data/epw_to_js.py`，用法：`python epw_to_js.py 输入.epw 输出.js`）：只取 EPW 第 14（DNI）、15（DHI）列，8,760 小时，取整到 1 Wh/m²。全年 GHI 1,263.2、DNI 1,244.9、DHI 568.2 kWh/m²。

## 季节风（2026-10-19 起，体块推演的“风”显示）
- 同一个机场气象文件（`Passivehouse_Tool/02_Data/EPW/CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw`），只取第 21 列（风向）和第 22 列（风速）。没有重新下载。
- 转换：`03_Data/epw_wind_to_js.py`（用法：`python epw_wind_to_js.py 输入.epw`，输出一行 `const WIND = {...};`）。汇总成全年和四季的 16 方位小时占比、平均风速，以及朝北、东、南、西立面的迎风时间和平均迎面风速。
- 站点测在 10 m 高、开阔地，没有按场地修正。
- 2026-10-19 更新：`epw_wind_to_js.py` 改为输出逐小时风向、风速（`const WIND_RAW`），统计和动画在工具里按日期范围、使用时段算。
