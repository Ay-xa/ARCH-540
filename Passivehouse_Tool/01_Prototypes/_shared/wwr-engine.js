// wwr-engine.js — 窗墙比推敲器的共享计算引擎（Passivehouse_Tool/01_Prototypes/_shared）
// 2026-09-30 从 Version_06/wwr-tool.html 抽出。Version_06 自己的文件没有改动，仍用它内部的同一份代码；
// 本文件供 Zoning 分支（以及将来愿意改用共享文件的版本）使用。方法与取值的说明见 PLAN_v06.md 和 Zoning/Version_01/PLAN_z01.md。
//
// 约定：
//  1 引擎不读、不写任何界面状态。所有输入通过参数传入（V06 的 calc() 直接读全局 S，这是两者原来分不开的原因）。
//  2 引擎里没有任何功能名称、房间名称、朝向规则。适合度评分只按配置表的 functions 数组循环。
//  3 标注「逐字复制」的函数与 Version_06 对应函数一字不差（_shared/verify_extract.py 逐字比对）；
//    标注「通用化」的函数说明了与 V06 的差别，并由 engine-test.html 用 V06 的 digest() 数值验证。
//  4 依赖 wwr-climate.js（T_HOT / CLIM / HOURLY），必须先加载。
//
// 对外接口：window.WWR = { 常数与工具, sunFor, simulateHours, windowsFromWwr, calcSegment, calcFacadeFromWwr,
//                          aggregateBuilding, segmentsForWall, gridCells, gridConditions, COND, suitability, suitGrid, stripMean, digestV06 }

(function(){
"use strict";
if(typeof CLIM==='undefined'||typeof HOURLY==='undefined'){throw new Error('wwr-engine.js 需要先加载 wwr-climate.js');}

/* ===== 常数（逐字复制 V06） ===== */
const DIRS=['北','东北','东','东南','南','西南','西','西北'];
// 被动房判据：室内 > 25 °C 的小时数不超过全年 10%，建议 5% 以下（Passipedia / Passivhaus Trust，已核对）。
const OVH_LIMIT=10, OVH_GOOD=5;
function ovhScore(pct){return 100*Math.max(0,Math.min(1,1-pct/OVH_LIMIT));}   // 0% → 100 分，5% → 50 分，≥10% → 0 分
// 热质量：单位房间面积的有效热容 Wh/(m²K)。估计值，量级参考 ISO 13790 的建筑热容分类（轻≈110、中≈165、重≈260 kJ/m²K），未逐一核对。
const MASS={light:{label:'轻',hint:'木框架、石膏板内衬',c:30},mid:{label:'中',hint:'混凝土楼板露出',c:50},heavy:{label:'重',hint:'混凝土楼板 + 砌体墙',c:75}};
// 开窗通风：室内比室外热 1 K 以上且室内 > 22 °C 时的额外换气次数 1/h。假设值。
const VENT={none:{label:'不开窗',hint:'只有卫生通风',ach:0},win:{label:'开窗',hint:'室内比室外热时开窗，约 2 次/h',ach:2},cross:{label:'穿堂风',hint:'对开窗形成穿堂风，约 4 次/h',ach:4}};
const HOT_TIP=12; // 仍用于详情面板文字

/* ===== 工具函数（逐字复制 V06） ===== */
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const rad=d=>d*Math.PI/180;
const norm=a=>((a%360)+360)%360;
function interpN(arr,az){const n=arr.length,st=360/n;az=norm(az);const i=Math.floor(az/st),t=(az-i*st)/st;return arr[i%n]*(1-t)+arr[(i+1)%n]*t;}
function dirName(az){return DIRS[Math.round(norm(az)/45)%8];}

/* ===== 太阳位置（逐字复制 V06；NOAA 简化公式，与 epw_to_clim.py 相同） ===== */
function sunPos(lat,lon,tz,doy,hour){
  const g=2*Math.PI/365*(doy-1+(hour-12)/24);
  const eqt=229.18*(0.000075+0.001868*Math.cos(g)-0.032077*Math.sin(g)-0.014615*Math.cos(2*g)-0.040849*Math.sin(2*g));
  const decl=0.006918-0.399912*Math.cos(g)+0.070257*Math.sin(g)-0.006758*Math.cos(2*g)+0.000907*Math.sin(2*g)-0.002697*Math.cos(3*g)+0.00148*Math.sin(3*g);
  const tst=hour*60+eqt+4*lon-60*tz, ha=rad(tst/4-180), la=rad(lat);
  const sa=Math.sin(la)*Math.sin(decl)+Math.cos(la)*Math.cos(decl)*Math.cos(ha);
  const x=-Math.sin(ha)*Math.cos(decl), y=Math.sin(decl)*Math.cos(la)-Math.cos(decl)*Math.sin(la)*Math.cos(ha);
  return [Math.asin(clamp(sa,-1,1))*180/Math.PI, norm(Math.atan2(x,y)*180/Math.PI)];
}
const SUN={};
function sunFor(key){ // 每个气象站只算一次全年 8760 小时的太阳高度角 / 方位角
  if(SUN[key]) return SUN[key];
  const c=CLIM[key], alt=new Float32Array(8760), az=new Float32Array(8760);
  for(let i=0;i<8760;i++){const p=sunPos(c.lat,c.lon,c.tz,Math.floor(i/24)+1,(i%24)+0.5);alt[i]=p[0];az[i]=p[1];}
  return SUN[key]={alt,az};
}

/* ===== 室内温度逐小时模拟（单节点热平衡）=====
   通用化：V06 的 simulateHours(p,hr,sun) 只有一种窗（p.Ag 总玻璃面积、p.hw 一个窗高，挑檐遮挡按这个窗高算）。
   这里的 p.groups = [{Ag, hw}, …]：同尺寸的窗归为一组，各组分别算挑檐遮挡后的直射再相加。
   只有一组时，每一步的算式与 V06 完全相同（求和只有一项），数值逐位相等——engine-test.html 用 V06 digest 验证。
   其余公式逐字同 V06：
   C·ΔT = Q_sol + Q_int − (H_tr + H_ve)·(T_i − T_e)，每小时一步，隐式求解：T_i,new = (C·T_i + Q_sol + Q_int + H·T_e) / (C + H)
   卫生通风 nHyg 常开；室外比室内热时按热回收效率 etaHR 折减；开窗通风只在室内比室外热 1 K 以上且室内 > 22 °C 时启用。采暖季室温不低于 20 °C。 */
function simulateHours(p,hr,sun){
  const groups=p.groups||[{Ag:p.Ag,hw:p.hw}], nG=groups.length;
  const scr=(p.screen==null)?1:clamp(p.screen,0,1);   // 2026-09-30 新增：固定外屏（如穿孔板）的透光系数，默认 1 = 无屏，数值与 V06 相同
  // 2026-10-01 新增：每组窗可带自己的挑檐与透光系数（G.oh 外缘深度、G.ohIn 内缘离墙距离、G.ohGap 挑檐到窗头距离、G.ohOp 挑檐不透光率、G.scr 透光系数）；缺省回落到段的 p.oh / 0 / 0.05 / 1 / scr，此时算式与 V06 相同
  const gOh=G=>G.oh!=null?G.oh:p.oh, anyOh=groups.some(G=>gOh(G)>0);
  const fsh=(x,gap,h,t)=>clamp((x*t-gap)/h,0,1);
  let Ti=20, h25=0, Tmax=-99, Qsol_a=0;
  for(let i=0;i<8760;i++){
    const Te=hr.T[i]/10; let Qsol=0;
    const al=sun.alt[i];
    if(al>0&&(hr.G[i]>0||hr.B[i]>0)){
      const cd=Math.cos(rad(sun.az[i]-p.az)), c=Math.cos(rad(al))*cd;
      const beam0=c>0?hr.B[i]*c:0;
      const prof=(beam0>0&&anyOh)?Math.atan(Math.tan(rad(al))/cd)*180/Math.PI:0;
      for(let gI=0;gI<nG;gI++){const G=groups[gI];let beam=beam0;const oh=gOh(G);
        if(beam>0&&oh>0){const t=Math.tan(rad(prof)),gap=G.ohGap!=null?G.ohGap:0.05,op=G.ohOp!=null?G.ohOp:1,inn=G.ohIn||0;
          beam*=1-op*(fsh(oh,gap,G.hw,t)-(inn>0?fsh(inn,gap,G.hw,t):0));}
        Qsol+=G.Ag*p.g*0.8*(beam+hr.D[i]*0.5+hr.G[i]*0.2*0.5)*(G.scr!=null?G.scr:scr);}
    }
    let ach=p.nHyg*(Te<Ti?1:(1-p.etaHR));
    if(p.ventAch>0&&Ti>Te+1&&Ti>22) ach+=p.ventAch;
    const H=p.Htr+0.33*ach*p.V;
    Ti=(p.C*Ti+Qsol+p.Qint+H*Te)/(p.C+H);
    if(Ti<20) Ti=20;
    if(Ti>25) h25++; if(Ti>Tmax) Tmax=Ti; Qsol_a+=Qsol;
  }
  return {h25, ovh:h25/87.6, Tmax, Qsol:Qsol_a/1000, Htr:p.Htr};
}

/* ===== 从窗墙比生成窗户（V06 calc() 前 6 行的规则，含它的三处截断）=====
   输入：墙长 len、窗墙比 wwr、每层窗数 n、窗台 sill、窗头 head、层高 H。
   输出：{windows:[{u,w,h,sill}], wi, hw, totW, clamped, has}。窗从室外看从左到右均匀布置，第 i 扇中心在 (i+0.5)/n·len（与 V06 平面图一致）。
   V06 的截断在这里体现（这是它的"默认方案"定义的一部分，不是引擎的行为）：
     窗头 ≤ 吊顶（H − 0.3）；窗台 ≤ 窗头 − 0.4（最小窗高 0.4）；总窗宽 ≤ 墙长 90%。
   V06 的 has 规则：wwr > 0 且单窗宽 > 0.05，否则视为无窗（返回空数组，但仍给出 wi / totW 供显示）。 */
function windowsFromWwr(len,wwr,n,sill0,head0,H){
  const Hc=H-0.3;
  const head=Math.min(head0,Hc), sill=Math.min(sill0,head-0.4), hw=head-sill;
  let totW=wwr*len*H/hw; const maxW=len*0.9, clamped=totW>maxW+1e-9; totW=Math.min(totW,maxW);
  const wi=n>0?totW/n:0, has=wwr>0&&wi>0.05;
  const windows=[];
  if(has) for(let i=0;i<n;i++){const c=(i+.5)/n*len;windows.push({u:c-wi/2,w:wi,h:hw,sill});}
  return {windows,wi,hw,totW,clamped,has,n};
}

/* ===== 一段墙的计算（通用化的 V06 calc()）=====
   seg = { len 墙段长 m, az 方位角 °, oh 挑檐 m, windows:[{w,h,sill}], mass?, vent? }
   ctx = { H 层高, floors 层数, depth 房间进深, A 计算假设(同 V06 S.A), clim 气候键, mass, vent }
   与 V06 的差别只有一处：窗的尺寸由 seg.windows 直接给出，不再从窗墙比反推、也不做任何截断（越界由前端校验报告）。
   同尺寸的窗归为一组；每组内的算式与 V06 的"单窗 × N"完全相同，组间相加。只有一组时全部字段与 V06 逐位相等
  （totW / gap 除外：V06 先算 totW 再除 n，这里反过来乘回去，n 为 2 的幂时也相等）。
   过热模拟：整段墙上的所有窗合成一个房间（房间面积 = 段长 × 进深 × 层数），与 V06 把一面墙当一个房间相同。 */
function calcSegment(seg,ctx){
  const A=ctx.A, len=seg.len, az=norm(seg.az), H=ctx.H, Hc=H-0.3, floors=ctx.floors, depth=ctx.depth, oh=seg.oh||0;
  // 2026-09-30 新增：seg.screen = 固定外屏（穿孔板等）的透光系数 0–1，对直射、散射、采光一起折减；缺省 1 = 无屏，所有数值与 V06 相同
  const scr=(seg.screen==null)?1:clamp(seg.screen,0,1);
  const scrD=(seg.screenDay==null)?scr:clamp(seg.screenDay,0,1);   // 采光可用单独的透光系数（穿孔板对漫射光的透过率低于开孔率）；缺省与 screen 相同
  // 分组：w,h,sill 完全相同的窗归一组
  const groups=[];
  // 2026-10-01：每扇窗可选字段 screen / screenDay / oh / ohIn / ohGap / ohOpacity（部分窗在屏后、部分窗在挑檐下）；缺省回落到段级取值
  const same=(a,b)=>a.w===b.w&&a.h===b.h&&a.sill===b.sill&&a.scr===b.scr&&a.scrD===b.scrD&&a.oh===b.oh&&a.ohIn===b.ohIn&&a.ohGap===b.ohGap&&a.ohOp===b.ohOp;
  (seg.windows||[]).forEach(wn=>{if(!(wn.w>0.05)) return; // V06 has 规则：窗宽 ≤ 0.05 视为无窗
    const gs=wn.screen!=null?clamp(wn.screen,0,1):scr, gsD=wn.screenDay!=null?clamp(wn.screenDay,0,1):(wn.screen!=null?gs:scrD);
    const cand={w:wn.w,h:wn.h,sill:wn.sill,scr:gs,scrD:gsD,oh:wn.oh!=null?wn.oh:oh,ohIn:wn.ohIn||0,ohGap:wn.ohGap!=null?wn.ohGap:0.05,ohOp:wn.ohOpacity!=null?wn.ohOpacity:1};
    const g=groups.find(x=>same(x,cand));if(g)g.count++;else groups.push(Object.assign(cand,{count:1}));});
  const has=groups.length>0;
  const n=groups.reduce((a,g)=>a+g.count,0);
  // 每组：单窗几何（逐字同 V06），再 × N = count × floors
  let AwT=0,AgT=0,AfT=0,lgT=0,PT=0,totW=0;
  groups.forEach(g=>{const wi=g.w,hw=g.h;
    const gw=Math.max(0,wi-2*A.fw), gh=Math.max(0,hw-2*A.fw);
    const Aw1=wi*hw, Ag1=gw*gh, Af1=Aw1-Ag1, lg1=(gw>0&&gh>0)?2*(gw+gh):0, P1=2*(wi+hw), N=g.count*floors;
    g.Aw1=Aw1;g.Ag1=Ag1;g.Af1=Af1;g.lg1=lg1;g.N=N;g.AwT=Aw1*N;g.AgT=Ag1*N;g.head=g.sill+hw;
    g.Uw=(Ag1*A.Ug+Af1*A.Uf+lg1*A.psig)/Aw1;
    AwT+=g.AwT;AgT+=g.AgT;AfT+=Af1*N;lgT+=lg1*N;PT+=P1*N;totW+=wi*g.count;});
  const Uw=has?(groups.length===1?groups[0].Uw:(AgT*A.Ug+AfT*A.Uf+lgT*A.psig)/AwT):0;
  const frameFrac=has?AfT/AwT:0;
  const wwrAct=AwT/(len*H*floors);
  const c=CLIM[ctx.clim],Gw=interpN(c.GW,az),Gs=interpN(c.GS,az),dW=interpN(c.DW,az),dS=interpN(c.DS,az),pW=interpN(c.PW,az),pS=interpN(c.PS,az);
  const gH=interpN(c.GH,az),dH=interpN(c.DH,az),pH=interpN(c.PH,az);
  // 挑檐遮挡按每组窗高算；立面级 sh*/fs* 按玻璃面积加权（一组时即该组的值）
  const shadeG=(g,p)=>{if(!(g.oh>0))return 0;const t=Math.tan(rad(p)),f=x=>clamp((x*t-g.ohGap)/g.h,0,1);return g.ohOp*(f(g.oh)-(g.ohIn>0?f(g.ohIn):0));};
  let Qgain=0,Qsum=0,Qhot=0,shWa=0,shSa=0,shHa=0;
  groups.forEach(g=>{const shW=shadeG(g,pW),shS=shadeG(g,pS),shH=shadeG(g,pH),fsW=1-dW*shW,fsS=1-dS*shS,fsH=1-dH*shH;
    g.shW=shW;g.shS=shS;g.shH=shH;g.fsW=fsW;g.fsS=fsS;g.fsH=fsH;
    Qgain+=g.AgT*A.g*0.8*Gw*fsW*0.9*g.scr; Qsum+=g.AgT*A.g*0.8*Gs*fsS*g.scr; Qhot+=g.AgT*A.g*0.8*gH*fsH*g.scr;
    shWa+=shW*g.AgT;shSa+=shS*g.AgT;shHa+=shH*g.AgT;});
  const shW=has&&AgT>0?shWa/AgT:0, shS=has&&AgT>0?shSa/AgT:0, shH=has&&AgT>0?shHa/AgT:0, fsW=1-dW*shW, fsS=1-dS*shS, fsH=1-dH*shH;
  const Qloss=has?((Uw-A.Uwall)*AwT+A.psiI*PT)*A.Gt:0;
  const net=Qgain-Qloss, netPer=AwT>0?net/AwT:null;
  const zoneA=len*depth*floors, sumPer=Qsum/zoneA, hotPer=Qhot/zoneA, lossPer=Qloss/zoneA;
  const mass=MASS[seg.mass||ctx.mass], vent=VENT[seg.vent||ctx.vent];
  const Htr=A.Uwall*(len*H*floors-AwT+len*depth)+(has?Uw*AwT+A.psiI*PT:0);
  const sim=simulateHours({az,groups:has?groups.map(g=>({Ag:g.AgT,hw:g.h,oh:g.oh,ohIn:g.ohIn,ohGap:g.ohGap,ohOp:g.ohOp,scr:g.scr})):[{Ag:0,hw:1}],g:A.g,oh,Htr,V:zoneA*Hc,C:mass.c*zoneA,Qint:A.qint*zoneA,nHyg:A.nHyg,etaHR:A.etaHR,ventAch:vent.ach,screen:scr},HOURLY[ctx.clim],sunFor(ctx.clim));
  // 采光：每组按自己的可见天空角，按每米墙玻璃面积相加（一组时 = V06 的 vt·agPerM·theta·0.9/(Asurf·0.75)）
  const Asurf=2*depth+2*Hc;
  let DF=0,agPerM=0,thetaA=0,alphaTopA=0;
  groups.forEach(g=>{const agM=g.Ag1*g.count/len;const alphaTop=g.oh>0?(g.ohOp*Math.atan((g.h/2+g.ohGap)/g.oh)*180/Math.PI+(1-g.ohOp)*90):90;const theta=Math.max(0,alphaTop-A.obs);   // 挑檐不透光率 < 1 时（穿孔板翻开），被挡的天空按透光部分折回
    g.theta=theta;g.alphaTop=alphaTop;DF+=A.vt*agM*theta*0.9/(Asurf*0.75)*g.scrD;agPerM+=agM;thetaA+=theta*g.Ag1*g.count;alphaTopA+=alphaTop*g.Ag1*g.count;});
  const agSum=groups.reduce((a,g)=>a+g.Ag1*g.count,0);
  const theta=has&&agSum>0?thetaA/agSum:(oh>0?Math.max(0,Math.atan((0.9+0.05)/oh)*180/Math.PI-A.obs):Math.max(0,90-A.obs));
  const alphaTop=has&&agSum>0?alphaTopA/agSum:(oh>0?Math.atan((0.9+0.05)/oh)*180/Math.PI:90);
  // 窗头 / 窗台 / 窗高 / 单窗宽：一组时就是该组；多组时按窗面积加权（显示用）
  const wAw=groups.reduce((a,g)=>a+g.AwT,0);
  const head=has?groups.reduce((a,g)=>a+g.head*g.AwT,0)/wAw:Math.min(2.4,Hc), sill=has?groups.reduce((a,g)=>a+g.sill*g.AwT,0)/wAw:0.6, hw=head-sill;
  const wi=has?groups.reduce((a,g)=>a+g.w*g.AwT,0)/wAw:0;
  const limit=2.5*head, cover=Math.min(1,limit/depth);
  const gap=has?(len-totW)/n:len;
  const uni=has?clamp(1-Math.max(0,gap-0.5*head)/(1.5*head),0,1):0;
  const sc={
    day:has?100*(0.65*Math.min(1,DF/3)+0.25*cover+0.10*uni):0,
    loss:100*clamp(1-lossPer/20,0,1),
    gain:netPer==null?null:100*clamp((netPer+40)/100,0,1),
    heat:ovhScore(sim.ovh)
  };
  return {len,az,oh,screen:scr,screenDay:scrD,head,sill,hw,totW,n,wi,has,Uw,frameFrac,AwT,AgT,PT,wwrAct,Gw,Gs,dW,dS,pW,pS,shW,shS,fsW,fsS,
    Qgain,Qloss,net,netPer,Qsum,sumPer,Qhot,hotPer,gH,dH,pH,shH,fsH,lossPer,zoneA,sim,ovh:sim.ovh,h25:sim.h25,TmaxIn:sim.Tmax,Htr,DF,theta,alphaTop,limit,cover,gap,uni,sc,Hc,
    Wx:zoneA>0?Qgain/zoneA:0, Hx:hotPer,   // 网格 / 分区用的两个暴露度别名（与 V06 gridConditions 的定义相同）
    groups:groups.map(g=>({w:g.w,h:g.h,sill:g.sill,count:g.count,Aw1:g.Aw1,Ag1:g.Ag1,Uw:g.Uw,theta:g.theta,scr:g.scr,scrD:g.scrD,oh:g.oh,ohIn:g.ohIn,ohGap:g.ohGap,ohOp:g.ohOp})),
    hourly:null};   // 预留：建议层那一轮填"月 × 钟点"分布
}

/* ===== V06 等价层：用 V06 的一组立面参数算整面墙 =====
   fac = {wwr, n, oh, mass?, vent?}，其余同 ctx，另需 sill / head（V06 四面共用的窗台 / 窗头）。
   返回 calcSegment 的结果，并把 V06 特有的 F / clamped / k 字段补上，字段集合与 V06 calc(k) 一致（用于 digest 比对）。 */
function calcFacadeFromWwr(k,len,az,fac,ctx){
  const gen=windowsFromWwr(len,fac.wwr,fac.n,ctx.sill,ctx.head,ctx.H);
  const r=calcSegment({len,az,oh:fac.oh,windows:gen.windows,mass:fac.mass,vent:fac.vent},ctx);
  r.k=k; r.F=Object.assign({},fac); r.clamped=gen.clamped;
  if(!gen.has){ // V06 无窗时仍报告反推出的尺寸（wi / totW / n / head / sill / hw）
    const Hc=ctx.H-0.3, head=Math.min(ctx.head,Hc), sill=Math.min(ctx.sill,head-0.4);
    r.head=head;r.sill=sill;r.hw=head-sill;r.totW=gen.totW;r.n=fac.n;r.wi=gen.wi;
    r.limit=2.5*head;r.cover=Math.min(1,r.limit/ctx.depth);r.gap=gen.has?(len-gen.totW)/fac.n:len;
    const alphaTop=fac.oh>0?Math.atan((r.hw/2+0.05)/fac.oh)*180/Math.PI:90;r.alphaTop=alphaTop;r.theta=Math.max(0,alphaTop-ctx.A.obs);
  }
  return r;
}

/* ===== 整栋汇总（逐字同 V06 calcAll() 的汇总部分）=====
   R = {S:{…},E:{…},N:{…},W:{…}} 或任意墙键的结果集合（每项须有 AwT, len, net, Qsum, Qhot, ovh, zoneA, DF）；box = {L, W, H, floors} */
function aggregateBuilding(R,keys,box){
  const Htot=box.H*box.floors, gross=box.L*box.W*box.floors, TFA=gross*0.85;
  let Aw=0,Awall=0,net=0,sum=0,hot=0,dfw=0,lw=0,ovh=0,za=0;
  keys.forEach(k=>{const r=R[k];Aw+=r.AwT;Awall+=r.len*Htot;net+=r.net;sum+=r.Qsum;hot+=r.Qhot;ovh+=r.ovh*r.zoneA;za+=r.zoneA;dfw+=r.DF*r.len;lw+=r.len;});
  const Aenv=2*box.L*box.W+2*Htot*(box.L+box.W), V=box.L*box.W*Htot;
  return {wwr:Aw/Awall,net,sumPer:sum/TFA,hotPer:hot/TFA,ovh:ovh/za,DF:dfw/lw,AV:Aenv/V,TFA};
}

/* ===== 立面段划分（PLAN_z01 §3.1，已确认的 B：窗段与空墙段交替）=====
   wall = {id, length}, windows = 该墙上的窗 [{key,u,w,h,sill}]（假定已通过校验：不越界、不重叠）。
   返回按 u 排序的段数组：{kind:'window'|'blank', u0, u1, len, windows:[…], id}。长度 0 的空墙段不生成。 */
function segmentsForWall(wall,windows){
  const ws=windows.slice().sort((a,b)=>a.u-b.u), segs=[]; let cur=0;
  ws.forEach((w,i)=>{
    if(w.u>cur+1e-9) segs.push({kind:'blank',u0:cur,u1:w.u,len:w.u-cur,windows:[],id:`seg:${wall.id}:blank:${segs.length}`});
    segs.push({kind:'window',u0:w.u,u1:w.u+w.w,len:w.w,windows:[w],id:`seg:${w.key!=null?w.key:wall.id+':'+i}`});
    cur=w.u+w.w;});
  if(wall.length>cur+1e-9||!segs.length) segs.push({kind:'blank',u0:cur,u1:wall.length,len:wall.length-cur,windows:[],id:`seg:${wall.id}:blank:${segs.length}`});
  return segs;
}

/* ===== 平面条件网格（通用化的 V06 gridCells / gridConditions；方法见 PLAN_zoning.md §3–4）=====
   通用化只是把 V06 里读全局 S.L / S.W / S.grid / S.depth 的地方改为参数 box = {L, W, depth, grid}；公式逐字同 V06。
   R 是四面墙的整墙结果（键 S/E/N/W，矩形体块）。将来按段分配光源时，只需给这里换输入，核心 kernelCell / sunPatch 不变。 */
const ZG={lamFac:1.0, mix:0.5};
function kernelCell(a,b,D,lam,patch){
  const lo=Math.max(0,a), hi=Math.min(D,b), w=b-a;
  if(hi<=lo||w<=0) return {phi:0,u:0,one:0};
  const phi=(Math.exp(-lo/lam)-Math.exp(-hi/lam))*D/(1-Math.exp(-D/lam))/w;
  let u=phi; // 直射条带无效（太阳太高、房间太浅）时退回衰减曲线
  if(patch&&patch.d2>patch.d1+1e-9){const o=Math.max(0,Math.min(hi,patch.d2)-Math.max(lo,patch.d1));u=o*D/(patch.d2-patch.d1)/w;}
  return {phi,u,one:(hi-lo)/w};
}
function sunPatch(sill,head,p,D){const t=Math.tan(rad(p));if(!(t>1e-6))return null;const d1=sill/t,d2=Math.min(D,head/t);return d1<D-1e-9?{d1,d2}:null;}
const KEYS4=['S','E','N','W'];
function gridCells(box){
  const nx=Math.max(1,Math.round(box.L/box.grid)), ny=Math.max(1,Math.round(box.W/box.grid)), gx=box.L/nx, gy=box.W/ny, cells=[];
  for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
    const x=-box.L/2+(i+.5)*gx, y=-box.W/2+(j+.5)*gy;
    cells.push({i,j,x,y,gx,gy,area:gx*gy,d:{S:box.W/2-y,N:box.W/2+y,E:box.L/2-x,W:box.L/2+x},DFk:{},Wxk:{},Hxk:{},DF:0,Wx:0,Hx:0});
  }
  return {nx,ny,gx,gy,cells};
}
function gridConditions(R,box){
  const G=gridCells(box), D=box.depth;
  const P={};
  KEYS4.forEach(k=>{const r=R[k];
    P[k]={DF:r.DF, lam:ZG.lamFac*r.head,
      gain:r.zoneA>0?r.Qgain/r.zoneA:0, dirW:r.fsW>0?r.dW*(1-r.shW)/r.fsW:0, patchW:sunPatch(r.sill,r.head,r.pW,D),
      hot:r.hotPer, dirH:r.fsH>0?r.dH*(1-r.shH)/r.fsH:0, patchH:sunPatch(r.sill,r.head,r.pH,D)};
  });
  G.cells.forEach(c=>{
    KEYS4.forEach(k=>{const p=P[k], half=(k==='S'||k==='N')?c.gy/2:c.gx/2, d=c.d[k];
      const kd=kernelCell(d-half,d+half,D,p.lam,null);
      const kw=kernelCell(d-half,d+half,D,p.lam,p.patchW), kh=kernelCell(d-half,d+half,D,p.lam,p.patchH);
      const gainK=ZG.mix*kw.one+(1-ZG.mix)*(p.dirW*kw.u+(1-p.dirW)*kw.phi);
      const hotK=ZG.mix*kh.one+(1-ZG.mix)*(p.dirH*kh.u+(1-p.dirH)*kh.phi);
      c.DFk[k]=p.DF*kd.phi; c.Wxk[k]=p.gain*gainK; c.Hxk[k]=p.hot*hotK;
      c.DF+=c.DFk[k]; c.Wx+=c.Wxk[k]; c.Hx+=c.Hxk[k];
    });
  });
  G.cells.forEach(c=>{c.inStrip=KEYS4.some(k=>c.d[k]<=D+1e-9);});   // Version_06：是否在任一房间带内（needsWindow 用）；不改任何数值
  G.max={DF:Math.max(0,...G.cells.map(c=>c.DF)),Wx:Math.max(0,...G.cells.map(c=>c.Wx)),Hx:Math.max(0,...G.cells.map(c=>c.Hx))};
  G.per=P; G.D=D;
  return G;
}

/* ===== 适合度评分（逐字复制 V06；只按配置表循环，不含功能名） ===== */
const COND={daylight:{key:'DF',label:'采光系数',unit:'%',dec:1},winter:{key:'Wx',label:'冬季得热',unit:' kWh/m²',dec:0},overheat:{key:'Hx',label:'夏季过热暴露',unit:' kWh/m²',dec:1}};
const ramp=(v,lo,hi)=>{const t=clamp((v-lo)/(hi-lo),0,1);return t*t*(3-2*t);};   // 平滑斜坡 0 → 1（对输入连续可导，减少边界抖动）
function condScore(v,c){const r=ramp(v,c.lo,c.hi);return 100*(c.dir==='down'?1-r:r);}
function suitability(cell,fn){let s=0,sw=0;const parts={};
  Object.keys(COND).forEach(ck=>{const c=fn[ck];if(!c||!(c.w>0)){parts[ck]=null;return;}const v=condScore(cell[COND[ck].key],c);parts[ck]=v;s+=c.w*v;sw+=c.w;});
  return {score:sw>0?s/sw:0,parts};}
function suitGrid(G,cfg){
  const F=cfg.functions,nF=F.length,cells=G.cells,n=cells.length,nx=G.nx,ny=G.ny;
  const total=cells.reduce((a,c)=>a+c.area,0);
  const raw=F.map(fn=>cells.map(c=>suitability(c,fn)));
  const R2=cfg.smoothRadius*cfg.smoothRadius+1e-9, rx=Math.round(cfg.smoothRadius/G.gx), ry=Math.round(cfg.smoothRadius/G.gy);
  const sm=F.map((fn,f)=>{const o=new Float64Array(n);for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){let s=0,c=0;
    for(let dj=-ry;dj<=ry;dj++){const jj=j+dj;if(jj<0||jj>=ny)continue;for(let di=-rx;di<=rx;di++){const ii=i+di;if(ii<0||ii>=nx)continue;if(di*di*G.gx*G.gx+dj*dj*G.gy*G.gy>R2)continue;s+=raw[f][jj*nx+ii].score;c++;}}
    o[j*nx+i]=s/c;}return o;});
  let affected=0;
  F.forEach((fn,f)=>{if(!fn.needsWindow)return;cells.forEach((c,i)=>{if(!c.inStrip){raw[f][i]={score:0,parts:{},noWindow:true};sm[f][i]=0;affected++;}});});
  const best=new Int16Array(n), second=new Int16Array(n).fill(-1), margin=new Float64Array(n), shares=new Array(nF).fill(0);
  for(let i=0;i<n;i++){let b=-1,bv=-Infinity,g=-1,gv=-Infinity;
    for(let f=0;f<nF;f++){const v=sm[f][i];if(v>bv){g=b;gv=bv;b=f;bv=v;}else if(v>gv){g=f;gv=v;}}
    best[i]=b;second[i]=g;margin[i]=g>=0?bv-gv:100;shares[b]+=cells[i].area/total;}
  return {raw,sm,best,second,margin,shares,affected,total};
}
function stripMean(G,SU,k,f){let s=0,a=0;G.cells.forEach((c,i)=>{if(c.d[k]<=G.D+1e-9){s+=SU.sm[f][i]*c.area;a+=c.area;}});return a?s/a:0;}

/* ===== V06 的 digest()：同样的 6 组（3 气候 × 2 预设）× 4 立面，用共享引擎算，输出与 V06 相同的键结构，用于逐字段比对 ===== */
const V06_DEFAULT={L:20,W:12,floors:3,H:3.0,rot:0,sill:0.6,head:2.4,depth:5,
  f:{S:{wwr:.40,n:4,oh:0},E:{wwr:.20,n:2,oh:0},N:{wwr:.15,n:2,oh:0},W:{wwr:.30,n:2,oh:0}},
  A:{Ug:.60,Uf:.80,psig:.035,fw:.11,g:.50,vt:.65,Uwall:.12,psiI:.04,obs:15,qint:2.1,nHyg:0.3,etaHR:0.75}};
function digestV06(){
  const D=V06_DEFAULT, out={};
  [['apNow','mid','win'],['hbNow','mid','win'],['f2080','mid','win'],['apNow','light','cross'],['hbNow','light','cross'],['f2080','light','cross']].forEach(([c,m,v])=>{
    const ctx={H:D.H,floors:D.floors,depth:D.depth,A:Object.assign({Gt:CLIM[c].Gt},D.A),clim:c,mass:m,vent:v,sill:D.sill,head:D.head};
    const R={};
    KEYS4.forEach(k=>{const len=(k==='S'||k==='N')?D.L:D.W, az=norm({S:180,E:90,N:0,W:270}[k]+D.rot);R[k]=calcFacadeFromWwr(k,len,az,D.f[k],ctx);});
    const o={};
    KEYS4.forEach(k=>{const r=R[k],row={};Object.keys(r).forEach(key=>{const x=r[key];if(typeof x==='number'||typeof x==='boolean')row[key]=x;else if(key==='sc'||key==='sim'||key==='F')row[key]=x;});o[k]=row;});
    o._=aggregateBuilding(R,KEYS4,{L:D.L,W:D.W,H:D.H,floors:D.floors}); out[`${c}|${m}|${v}`]=o;});
  return out;
}

window.WWR={DIRS,OVH_LIMIT,OVH_GOOD,ovhScore,MASS,VENT,HOT_TIP,clamp,rad,norm,interpN,dirName,sunPos,sunFor,simulateHours,
  windowsFromWwr,calcSegment,calcFacadeFromWwr,aggregateBuilding,segmentsForWall,
  ZG,kernelCell,sunPatch,KEYS4,gridCells,gridConditions,COND,ramp,condScore,suitability,suitGrid,stripMean,
  V06_DEFAULT,digestV06,version:'2026-10-01'};
})();
