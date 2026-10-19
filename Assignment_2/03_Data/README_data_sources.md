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
