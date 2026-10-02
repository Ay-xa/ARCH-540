# 读图收件夹（Massing_v01 读图 tab 的落地目录）

页面「读图」tab 上传的图和描述存在这里，每条一个文件夹：

```
inbox/<id>/
  img1.png …        用户上传的图
  request.json      {id, at, note, files[], status}
  card.json         参数卡（模型或 Claude Code 写；页面显示、用户改后写回）
```

`status`：`pending` 等读 → `read` 已有卡 → `applied` 已应用到设计 / `library` 已标记入库 / `claude` 需要 Claude 加新条目。

## 两种模式

- **api**：`Massing_v01/rhino/api_key.txt` 存在时，服务直接调模型（`server.py` 的 `vision_call`），上传即出卡。
- **claude**：没有 key 时，页面提示"在聊天里说「读图」"。Claude Code 在会话里读 `request.json` 和图，按 `SHADING_RULES.md` 的八个问题写 `card.json`，页面 3 s 内看到。

## card.json 的格式（两种模式一样）

```json
{
  "id": "<同文件夹名>", "at": "<时间>", "by": "claude-code 或 api:<模型>",
  "summary": "一两句话说这个装置怎么动",
  "answers": {"1 挡哪个方向的太阳": "", "2 元素的方向": "", "3 单元尺寸（宽 / 深 / 厚）": "", "4 单元密度与排布": "", "5 透不透（穿孔率）": "", "6 动不动（怎么动）": "", "7 在玻璃哪一侧": "", "8 盖住窗的哪部分": ""},
  "closest": "pivot | bifoldV | bifoldH | umbrella | none",
  "confidence": 0.8,
  "differences": ["和最接近条目的不同之处"],
  "evidence": ["图里看到的依据；估计值要说明"],
  "shading": {"type": "bifoldV", "unitW": 3.0, "tilt": 45, "tiltRange": [0, 90], "standoff": 0.4, "thick": 0.15, "skin": 3, "holeD": 5, "perfMin": 0.1, "perfMax": 0.3},
  "newEntryNeeded": false,
  "notes": "给设计者的一句提醒"
}
```

`shading` 的字段名和 `state.json` 的 `shading` 一致，页面「应用到设计」时直接写进去（装置类型 + 尺寸；按立面的开关和折角不动）。

## Claude Code 读图时的做法

1. 列出 `inbox/` 里 `status = pending` 的条目。
2. 用 Read 看图，对照 `SHADING_RULES.md` 的八个问题和 `MECHANISMS.md` 的四个条目。
3. 写 `card.json`（上面的格式），把 `request.json` 的 `status` 改为 `read`。
4. `newEntryNeeded = true` 时，在聊天里告诉用户要不要加新条目；加了就按 MECHANISMS.md 的流程做。

图片文件进 git（它们是用户的设计资料）；`api_key.txt` 不进。
