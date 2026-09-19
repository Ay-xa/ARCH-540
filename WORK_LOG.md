# ARCH 540 — Work Log

Records are appended after each session. Most recent entry is at the bottom.

---

## 2026-09-18

**Completed**
- Created `Unprotected_Opening_Tool/01_Prototypes/Version_04/index.html` based on V01
- Added Building Position sliders (Offset X / Offset Y, −1 to +1, mapped to full allowed range)
- Added orange ⚠ warning note in sidebar: BCBC table data not independently verified
- Replaced the oblique-projected 3D box in plan view with a proper **architectural isometric / axonometric view** (30°/60°, viewer from SE-above)
  - Parcel renders as flat ground parallelogram
  - Building renders as proper 3D box (roof + East face + South face visible)
  - LD annotation lines drawn on the ground plane from each facade midpoint to property line
  - Drag interaction updated with inverse isometric projection math so dragging follows the correct oblique direction (not the old orthographic formula)

**Key decisions**
- Isometric constants: `AXI = cos(π/6) ≈ 0.866`, `AYI = sin(π/6) = 0.5`; scale `isoSc` computed each render to fit parcel + building height in 800×560 viewBox
- Painter's algorithm order: North → West → East → South → Roof
- LD lines drawn on ground plane (z=0), not floating in 3D — cleaner and easier to read
- All elevations, BCBC calculations, sidebar inputs untouched

**Current state**
- V04 renders and runs without errors
- All four elevation cards (N/S/E/W) display correctly with PASS/FAIL badges
- Drag interaction works with correct isometric direction mapping
- V01, V02, V03 untouched in their folders

**Unresolved**
- ⚠ **BCBC 2024 table data in V01/V04 is UNVERIFIED** — carried from V01, never checked against the actual BCBC 2024 PDF. Must verify before any academic or submission use.
- Table C values are approximate (≈ Table B × 0.68) — source unclear
- LD annotation labels can overlap building geometry when building is near parcel edge — not a blocker but could be improved

**Next session: suggested starting point**
- Open `Unprotected_Opening_Tool/01_Prototypes/Version_04/index.html` in browser to review
- Decide whether to verify BCBC data (check Tables 3.2.3.1-B/C/D/E in BCBC 2024 PDF)
- Or continue with the next visual/UX improvement — possible candidates:
  - Add grid lines to the isometric ground plane
  - Show neighbour building outlines beyond the property line
  - Improve LD label placement in isometric view

---

## 2026-09-18 (session 2)

**Completed**
- Set up folder structure: `Unprotected_Opening_Tool/` with `01_Prototypes/`, `02_Current/`, `03_References/`, `04_Archive/`; `Version_01`/`Version_02` subfolders under `01_Prototypes` (user later added `Version_03` and `Map/` alongside these)
- Reviewed and compared the three opening-tool prototypes (V01 index.html, V02 facade_axo.html, V03 facade_checker.html) in plain language: functionality, tech stack (all vanilla HTML/CSS/JS, no framework), unique features, calculation-logic differences, reusable parts, and known issues/risks. Read-only — no files changed during this review.
- Opened and tested `Unprotected_Opening_Tool/01_Prototypes/Map/Version_01/bcbc_map_v2.html` (Vancouver parcel + zoning lookup via Leaflet + ArcGIS Open Data endpoints). Confirmed click-to-query works (tested on 3129 E 29th Ave → R1-1 zoning, 765 m², 10×33 m).
- Fixed "API KEY REQUIRED" basemap watermark in `Map/Version_01/bcbc_map_v2.html`: swapped the CARTO tile layer (now requires a key) for the free OpenStreetMap standard tile layer. Parcel/zoning query logic untouched.
- Created `Unprotected_Opening_Tool/01_Prototypes/Map/Version_02/bcbc_map_v2.html`: added a Leaflet layer-switcher control positioned under the zoom buttons (top-left), toggling between OpenStreetMap (default, no key needed) and the original CARTO layer (needs key, kept for future use). Verified both layers render and switch correctly; parcel/zoning click lookup still works in both.

**Key decisions**
- New map layer-switcher was built as a separate `Map/Version_02` rather than editing `Map/Version_01` further in place, so V01 stays as the minimal single-basemap reference.
- OpenStreetMap's standard tile server chosen as the default base layer since it needs no API key; CARTO kept as a selectable option in case an API key is obtained later.

**Current state**
- Opening-tool prototypes V01/V02/V03/V04 all untouched by this session except V04 pre-existed from session 1 above — no direction chosen yet, no integration started.
- `Map/Version_01` — basemap fixed, otherwise unchanged.
- `Map/Version_02` — new, adds layer switcher only; parcel/zoning logic identical to V01.

**Unresolved**
- The map tool's "Copy Params for V04" button is intended to feed `01_Prototypes/Version_04/index.html` — that file exists (see session 1 above) but the copy/paste hand-off between the two tools has not actually been tested end-to-end.
- No decision yet on which opening-tool prototype (or combination) to move forward with.
- CARTO layer still needs an API key if it's ever wanted as the default — currently just kept as a secondary, non-functional-without-key option in V02.

**Next session: suggested starting point**
- Decide on next direction for the opening-tool prototypes (verify BCBC data, or pick a prototype to build on)
- If continuing the map tool: test the actual "Copy Params for V04" → paste-into-V04 workflow end-to-end

---

## 2026-09-18 (session 3)

**Completed**
- Opened and reviewed `Map/Version_03/bcbc_map_v3.html` — adds local GeoJSON zoning overlay, point-in-polygon lookup, colour-coded districts, oriented bounding box, and loading overlay. File structure: HTML + separate `vancouver_zoning_wgs84.geojson` (2.5 MB).
- Diagnosed why V03 failed from `file://`: browser blocks `fetch()` calls to local files (CORS restriction).
- Created `Map/Version_04/bcbc_map_v4.html`: embedded the 2.5 MB GeoJSON directly into the HTML as an inline JavaScript variable. No `fetch()`, no server needed — double-click to open.
- Fixed basemap tile issue: OSM blocked requests from `file://` (usage policy) → CartoDB also now requires API key → switched to **Esri World Street Map** (`server.arcgisonline.com`), which is public, no key required, and consistent with the ArcGIS parcel API already used in the tool.
- Confirmed V4 works: 1621 zoning districts loaded, parcel click returns address / zoning / dimensions correctly.

**Key decisions**
- Esri tile layer chosen as the permanent basemap for V4 — no key, works from file://, same data source as the parcel query.
- GeoJSON embedding strategy chosen over local server: simpler workflow, no terminal commands needed before each session.
- V03 kept as reference for the "separate file + server" approach.

**Current state**
- `Map/Version_04/bcbc_map_v4.html` — fully self-contained, double-click to open, all features working ✓
- Map series: V01 (OSM fix) → V02 (layer switcher) → V03 (local GeoJSON, needs server) → V04 (embedded GeoJSON, standalone) ✓
- Opening-tool prototypes (V01–V04) untouched this session.

**Unresolved**
- "Copy Params for V04" → paste-into-opening-tool workflow still untested end-to-end.
- No decision yet on next direction for the opening-tool prototypes.
- ⚠ BCBC table data in opening-tool V04 still unverified against BCBC 2024 PDF.

**Next session: suggested starting point**
- Test "Copy Params for V04" button in Map V4, paste result into opening-tool V4 sliders — confirm the hand-off works
- Or: decide on next development direction (BCBC data verification, or next visual feature for opening-tool V4)

---

## 2026-09-18 (session 4)

**Completed**
- Created `Unprotected_Opening_Tool/01_Prototypes/Version_05/index.html` — a single self-contained HTML file merging Map V4 and Parcel Checker V4 into a two-tab layout.
- Tab 1 (Map): full Leaflet map with embedded GeoJSON zoning overlay and Esri basemap; parcel click loads address, zoning, and bounding-box dimensions in the side panel.
- Tab 2 (Parcel Checker): full BCBC compliance checker with isometric axonometric view, four elevation cards, all sliders.
- Bridge behaviour: selecting a parcel on the map auto-imports Parcel Width E-W and Depth N-S into Tab 2's sliders and switches to Tab 2 automatically. A green banner confirms the import (address + dimensions).
- "← Back to Map" button at the top of Tab 2's sidebar returns to the map; Leaflet `invalidateSize()` fires on return so tiles stay correct.
- Committed as `770c223`.

**Key decisions**
- Parcel Width/Depth are the only values auto-imported from the map; building size, height, occupancy, and neighbour setbacks remain manual in Tab 2.
- `importToChecker()` is injected directly after `showResult()` in the map's click handler, using `lastData.bbox` (already set by showResult) — no changes to showResult itself.
- File size ≈ 2.55 MB (GeoJSON embedded). Open by double-clicking in Chrome/Edge — in-app browser cannot handle files this large.
- "Parcel Checker" tool files are in `01_Prototypes/Parcel Checker/Version_04/` (not `Version_04/` directly as noted in earlier sessions).

**Current state**
- `Version_05/index.html` — fully functional two-tab merged tool ✓
- Map series: V01 → V02 → V03 → V04 (standalone) → V05 (merged with Checker)
- Parcel Checker series: V01 → V02 → V03 → V04 (isometric) → V05 (embedded in merged tool)

**Unresolved**
- ⚠ BCBC table data still unverified against BCBC 2024 PDF — all values carried from V01.
- The "Copy to Clipboard" button in the map panel is now secondary to auto-import but still present.
- No mobile layout tested (file is desktop-first).

**Next session: suggested starting point**
- Open `Version_05/index.html` in Chrome, click a parcel, confirm auto-jump and slider fill work end-to-end.
- Decide whether to verify BCBC table data (check Tables 3.2.3.1-B/C/D/E in BCBC 2024 PDF).

