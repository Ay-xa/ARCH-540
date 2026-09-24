# 气象数据（EPW）

窗墙比推敲器的气候数组全部由本文件夹中的 EPW 文件计算得出，生成脚本见 `../../03_Scripts/epw_to_clim.py`，输出 `../clim.json`，再由 `inject_clim.py` 写进工具文件。

| 文件 | 用途 | 来源 | 获取日期 |
|---|---|---|---|
| `CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw` | 当下（机场站），默认 | https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/CAN_Canada/BC_British_Columbia/CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.zip （zip 内 7 个文件，只保留 .epw） | 2026-09-24 |
| `CAN_BC_Vancouver.Harbour.CS.712010_TMYx.2009-2023.epw` | 当下（港口站） | Climate.OneBuilding.org 同一 BC 页面，`CAN_BC_Vancouver.Harbour.CS.712010_TMYx.2009-2023.zip`。原先存于课程 Google Drive（ARCH 522 Weather Data），2026-09-24 复制进项目 | 2024-07-16（原始下载） |
| `MORPHED_SSP585_2080s_CAN_BC_VANCOUVER-INTL-A_CWEC2020.epw` | 2080 年预测 | Pacific Climate Impacts Consortium，https://pacificclimate.org/data/weather-files ，SSP5-8.5 情景 2080 年代，由 CWEC2020 机场站文件移位生成。原先存于课程 Google Drive，2026-09-24 复制进项目 | 文件版本 3.0，生成于 2022-11-13 |

## 文件头（LOCATION 行）

```
Vancouver Intl AP,BC,CAN,CWEC2020,718920,49.19000,-123.1800,-8.0,4.3
VANCOUVER INTL A,BC,CAN,CWEC2020,718920,49.19,-123.18,-8.0,4.3          (2080)
Vancouver.Harbour.CS,BC,CAN,SRC-TMYx,712010,49.29528,-123.1219,-8.0,2.5
```

## 核对记录（2026-09-24）

- 机场站 CWEC2020 与 2080 移位文件逐小时比较：GHI、DNI、DHI 三列 8760 行完全相同；干球温度 8760 行全部不同，最大差 6.9 °C；露点、相对湿度、气压也不同。与 2080 文件头“只移位 TAS、RHS、DWPT、PS”的说明一致。
- 因此「当下（机场站）」与「2080 年预测」之间的差异只来自气温类变量；「当下（港口站）」与其他两者的差异还混有站点和数据集方法的差异。
