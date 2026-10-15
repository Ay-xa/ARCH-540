# Assignment 2

ARCH 540 第二次作业的工作文件夹。建于 2026-10-14，作业题目与方向待定，结构随设计推进再调整。

Assignment 1 的工具（MassShadeLight 及之前的原型）仍留在仓库根目录的 `Openning_Shade_Relation_Tool/`、`Passivehouse_Tool/` 等文件夹里，不搬动——GitHub Pages 的演示链接依赖那些路径。

## 文件夹分工

| 文件夹 | 放什么 |
|---|---|
| `00_Brief/` | 作业要求、评分标准、老师发的资料、课堂笔记。原件照原样放进来，不改名也可以。 |
| `01_Research/` | 调研与先例：参考项目、论文、网页截图、现场照片、自己的草图和想法记录。 |
| `02_Prototypes/` | 工具本身。每一版一个文件夹 `Version_01`、`Version_02`……，旧版不删、不覆盖，方便回头比较。 |
| `02_Prototypes/_shared/` | 几个版本共用的部分（比如计算引擎、公用样式）。只放确实被两个以上版本用到的东西。 |
| `02_Prototypes/Version_XX/rhino/` | 这一版配套的 Rhino / Grasshopper 文件和脚本（`.3dm`、`.gh`、`.py`、`state.json`），跟网页放在同一版文件夹里，搬家时一起搬。 |
| `03_Data/` | 数据：气候文件（EPW）、地图、底图、参考模型。大文件（几十 MB 以上）先问一下要不要进仓库。 |
| `04_Presentation/` | 对外展示：展板、汇报稿、最终提交稿。 |
| `04_Presentation/screenshots/` | 过程截图、GIF、渲染图，按日期或版本命名，例如 `2026-10-20_v01_plan.png`。 |

## 几条习惯

- **一版一个文件夹**：改动大就新开 `Version_02`，不要在 `Version_01` 里反复覆盖。小修可以在当前版本里改。
- **工作记录**仍写在仓库根目录的 `WORK_LOG.md`，每次结束工作时追加一段，不另开记录文件。
- **`.gitkeep`** 是空文件夹里的占位文件，Git 不记录空文件夹，有了它文件夹才会被上传。文件夹里有真东西之后可以删掉它，留着也无妨。
- 命名用英文、下划线、首字母大写（`Version_01`、`Site_Plan.png`），避免空格和中文文件名，Rhino 和网页读路径更稳。

## 待定

- 作业题目、交付要求（放 `00_Brief/` 后在这里补一句摘要和截止日期）。
- 是否沿用 Assignment 1 的共享引擎（`Passivehouse_Tool/01_Prototypes/_shared/`）：沿用就在 `_shared/` 里放一个说明指过去，不复制。
