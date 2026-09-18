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

