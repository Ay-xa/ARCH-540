// zoning-config.js — 室内自动分区的功能配置表（当前用途：公寓，整层简化为一个大户型）。
// 换用途只需替换本文件（或改 functions 数组），计算代码不写任何功能名称。方法与取值理由见 PLAN_zoning.md §5–7。
//
// 每种功能对三个条件各有一条评分曲线：
//   dir  'up' = 值越高越好，'down' = 值越低越好
//   lo,hi 分数从 0 升到 100（up）或从 100 降到 0（down）的区间，单位与条件相同（平滑斜坡，不是折线）
//   w    权重；三个条件的分数按权重平均得到 0–100 的适合度
// 条件单位：daylight 采光系数 %；winter 冬季太阳得热 kWh/(m² 房间面积·年)；overheat 高温时段透入辐射 kWh/(m²·年)。
// area 为目标面积占比区间；adjacency 为预留字段（本阶段不参与计算）。
// 所有阈值、权重、占比都是设计判断值，不是规范值。采光分级参考常见的采光系数经验分级（<2% 偏暗，2–5% 良好）。

window.ZONING_CONFIG = {
  use: 'apartment',
  label: '公寓（整层一个大户型）',
  version: 1,
  smoothRadius: 1.5,   // 分数空间平滑半径 m（去掉单格噪声，避免棋盘状）
  contiguity: 15,      // 连片强度 β：每米功能分界线的代价（分·m）。越大区域越成块、边界越短
  minRegion: 4,        // 最小成片面积 m²，更小的孤块并入相邻功能
  functions: [
    { key: 'living', label: '客厅', color: '--sun',
      daylight: { dir: 'up',   lo: 1.0, hi: 3.0, w: 1.0 },  // 3% 才满分：起居空间要明亮
      winter:   { dir: 'up',   lo: 5,   hi: 25,  w: 0.7 },  // 白天使用，希望晒到冬天的太阳
      overheat: { dir: 'down', lo: 5,   hi: 20,  w: 0.4 },  // 容忍度较高：白天在场、可主动遮阳
      area: { min: 0.30, max: 0.45 },                       // 客厅 + 餐厅 + 厨房
      adjacency: [],
      note: '光照最多、冬季得热好的区域' },
    { key: 'bedroom', label: '卧室', color: '--cold',
      daylight: { dir: 'up',   lo: 0.7, hi: 2.0, w: 0.7 },  // 2% 即满分：卧室不需要很亮
      winter:   { dir: 'up',   lo: 0,   hi: 20,  w: 0.3 },  // 白天少用，冬季得热只是轻微加分
      overheat: { dir: 'down', lo: 2,   hi: 10,  w: 1.0 },  // 最怕夜间过热：容忍度最低、权重最高
      area: { min: 0.30, max: 0.45 },
      adjacency: [],
      note: '光照略少、夏季过热风险低的区域；西向即使采光不错也不理想' },
    { key: 'service', label: '服务区', color: '--slab',
      daylight: { dir: 'down', lo: 0.5, hi: 2.5, w: 1.0 },  // 越暗越合适：不要占用亮的位置
      winter:   { dir: 'down', lo: 0,   hi: 20,  w: 0.4 },  // 不要占用晒得到冬天太阳的位置
      overheat: { dir: 'up',   lo: 0,   hi: 10,  w: 0.2 },  // 愿意承担热的位置，作为缓冲
      area: { min: 0.20, max: 0.35 },                       // 卫生间、储藏、走道、交通核
      adjacency: [],
      note: '光照最少的区域，通常在北侧或平面中部采光进深之外' }
  ]
};
