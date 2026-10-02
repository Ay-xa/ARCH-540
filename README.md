# MassShadeLight

**Demo (GitHub Pages, read-only snapshot):** https://ay-xa.github.io/ARCH-540/Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/massing-tool-en.html
(中文版 / Chinese interface: https://ay-xa.github.io/ARCH-540/Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/massing-tool.html)

The demo shows a saved design state with every panel of the tool. The live loop — move a slider, Rhino rebuilds the massing, Ladybug recounts sun hours — needs Rhino 8 on your own computer; see **How to use it**.

ARCH 540 (UBC SALA) design-tool project. The tool lives in `Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/`. Earlier prototypes that fed into it (window-wall-ratio tools, zoning, strip-window facade study) are kept in `Passivehouse_Tool/` and `Openning_Shade_Relation_Tool/` for reference.

---

## 1. Purpose

The tool connects the architect’s visual design process with real-time building performance feedback. By interactively adjusting building massing, window-to-wall ratio (WWR), and external shading devices, designers can directly observe how façade and form changes affect daylight availability and overheating risk within the building.

Using daylight and overheating as key design constraints, the tool provides simplified performance estimates informed by Passive House thermal comfort principles, including the guideline that indoor temperatures should not exceed 25°C for more than 10% of annual hours. Rather than replacing detailed energy simulation, the tool enables designers to understand the dynamic relationship between façade design, building massing, daylight, and thermal performance throughout the design process, supporting continuous design iteration.

---

## 2. How to use it

### What it is

Three parts that talk through one file, `rhino/state.json`:

| Part | File | Role |
|---|---|---|
| Web page | `massing-tool-en.html` (English) / `massing-tool.html` (中文) | sliders, plan heatmap, facade-segment table, window section, scheme comparison, image inbox |
| Local bridge | `rhino/server.py` (Python 3, standard library only) | serves the page on `http://localhost:8768`, validates every change, writes `state.json` |
| Rhino + Grasshopper | `rhino/massing.3dm`, `rhino/massing.gh` | rebuilds floors, windows and shading devices from `state.json`; Ladybug counts direct sun hours and writes them back |

Overheating and daylight are estimated on the page by a shared engine (`Passivehouse_Tool/01_Prototypes/_shared/wwr-engine.js`) from the wall segments Rhino writes back. Self-shading by the building’s own massing comes from Ladybug.

### Requirements

- Windows 10/11 (the launcher is a `.bat`; only Windows was tested).
- **Rhino 8** with Grasshopper (tested with Rhino 8.27).
- **Ladybug Tools** for Grasshopper (the `.gh` uses *LB Import EPW*, *LB Analysis Period*, *LB SunPath* and two *LB Direct Sun Hours*). Tested with the version installed on the author’s machine in 2026; if a Ladybug component appears as missing in your version, re-place it from your Ladybug tab and reconnect the same wires.
- **Python 3.10 or newer** on the PATH (tested with 3.13). No packages to install for the server.
- A browser (Chrome or Edge). The scheme list is stored in the browser.

### Run it

1. **Download the whole repository** (Code → Download ZIP, or `git clone`). Keep the folder structure: the page, the climate files and the shared engine find each other by relative paths.
2. Open `Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/rhino/` and **double-click `start_server.bat`**. A console window stays open and the browser opens `http://localhost:8768`. The status line should read *connected to local service*.
   If the page opens in Chinese, click **EN** at the top of the sidebar (and **中文** to switch back).
3. In Rhino 8, **open `rhino/massing.3dm`**, then open Grasshopper and **open `rhino/massing.gh`** from the same folder. The panel named `state.json` in the definition holds a relative name, so it works wherever the folder lives. Within a second the status line changes to *Rhino wrote back hh:mm:ss* and the plan, table and section fill in.
4. **Design**: move sliders in the sidebar (building size, floors, floor groups with setbacks and shifts, window-wall ratio, climate, room depth, shading device and its opening per facade, notches / courtyards / splits). Each change is written to `state.json`, Rhino rebuilds the model, the page re-reads the result. Ladybug sun hours take 10–60 s and arrive afterwards; untick *Calculate* → *Ladybug sun hours* if you want faster sliders.
   Red / blue / green points in Rhino are handles for notches, courtyards and splits; dragging them is the same as moving the sliders.
5. **Save scheme** keeps the current state in the browser. **Compare** shows 2–4 saved schemes side by side with the differences. **Read image** stores a picture of a shading device in `Openning_Shade_Relation_Tool/02_Rules/inbox/` so that a model (or a person) can turn it into a parameter card; nothing is sent anywhere unless you add your own API key file (see `rhino/server.py`).
6. Optional: `rhino/context_gen.py`, run in Rhino’s script editor, generates a 50 × 50 m lot with neighbouring houses, trees and people around the building for presentation renders (Arctic display mode). It is visual only and does not enter any calculation.

### If something does not move

- Status line says *Rhino 15 s without a write-back*: Grasshopper’s timer stopped. The watcher restarts itself; if it still sits, click the *Trigger* component once (pause) and again (play), or reopen `massing.gh`.
- *no local service*: the server console is closed, or port 8768 is taken by an earlier instance. Close the old console and run `start_server.bat` again.
- Rhino shows nothing after a parameter change: look at the `status` panel next to the *massing sync* component; it prints the reason (for example a notch that was ignored because it overlaps another one — the page marks those with ⚠ too).

---

## 3. Source

- **Passive House Institute China — “Passive House Requirements”**, https://phichina.com/passive-house-requirements.html (accessed 2026-10-02; the page carries no version number or date).
  Clause used: item **4, Thermal comfort** — *“not more than 10 % of the hours in a given year over 25 °C.”*
  The tool reports the share of hours above 25 °C as *overheating*; 10 % is drawn as the limit. The 5 % *recommended* target shown next to it is the tool’s own working value, not part of the cited page.
- Everything else is an assumption of the tool, not a regulation: the daylight-factor threshold (3 % shown as *sufficient*), the simplified hourly thermal model and its coefficients in `wwr-engine.js` (documented in `Passivehouse_Tool/01_Prototypes/_shared/ENGINE.md`), and the climate data from three Vancouver EPW files in `Passivehouse_Tool/02_Data/EPW/` (CWEC2020 airport, TMYx harbour, and a 2080s SSP5-8.5 morphed file; see the README in that folder).

---

## 4. One example

![MassShadeLight demo](Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/Massing_v01/screenshots/demo.gif)

Input (the state saved in `rhino/state.json`): 26 × 16 m footprint, 16 floors in 4 groups (ground floor and floor 4 set back), WWR 66 %, one notch on the east edge (5.5 m deep), one notch on the south edge (6.5 m deep, upper group only), one 5.5 × 5.0 m courtyard in the upper group, Vancouver airport climate.

Result for two shading devices on the same massing (from the *Compare* tab):

| | Hexagonal umbrella, 31° | Pivot panels, 31° |
|---|---|---|
| Overheating, no device | 10.2 % | 10.2 % |
| Overheating, with device | 4.2 % | 3.4 % |
| Daylight factor, with device | 3.48 % | 3.26 % |
| Summer direct sun on windows (Ladybug) | 254 h | 309 h |
| Device units | 204 | 237 |

Frames in the GIF: Rhino model with its context → sliders and plan heatmap → facade-segment table → section through the device with sun angles → topology operations in Rhino → scheme comparison. Still images are in `screenshots/`.

---

## 5. Skill and limits

**Reusable files**

- `Openning_Shade_Relation_Tool/02_Rules/SHADING_RULES.md` — how a shading device is described and turned into tool parameters.
- `Openning_Shade_Relation_Tool/02_Rules/MECHANISMS.md` — the device library (pivot, vertical knee fold, horizontal knee fold, hexagonal umbrella) and which parameters each one really uses.
- `Openning_Shade_Relation_Tool/02_Rules/inbox/README.md` — the eight-question parameter card a model fills in when reading a picture of a device.
- `Openning_Shade_Relation_Tool/01_Prototype/Strip_Window/PLAN_massing_v0*.md` and `WORK_LOG.md` — design decisions and the session-by-session record.

**What the tool does not do / where a person must check**

- Overheating and daylight are **estimates for comparing options**, not a simulation result. They use one room band along each facade, fixed internal gains and ventilation assumptions, and a simplified hourly model. Do not quote the numbers as absolute performance.
- Sun hours are **direct sun on the window band** (Ladybug Direct Sun Hours, no radiation, no sky model). Self-shading counts the building’s own floors and devices only; neighbouring buildings and the generated context are not in the calculation.
- Shading devices are geometric idealisations (opaque panels, one tilt per facade); perforation, materials and glare are not modelled.
- Only three Vancouver climate files are included. Other locations need their own EPW and a new climate entry in the engine.
- The thin-wall and overlap rules (1 m) for notches, courtyards and splits are drawing conveniences, not code requirements.
- The Pages demo is a saved snapshot: sliders there do not recompute. The live loop was tested on one Windows machine with Rhino 8.27.
