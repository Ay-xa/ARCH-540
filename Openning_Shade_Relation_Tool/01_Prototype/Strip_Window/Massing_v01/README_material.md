# README material (MassShadeLight)

Collected inputs for the README. Written by the user unless noted.

## 1. Purpose (user, 2026-10-02)

The tool connects the architect’s visual design process with real-time building performance feedback. By interactively adjusting building massing, window-to-wall ratio (WWR), and external shading devices, designers can directly observe how façade and form changes affect daylight availability and overheating risk within the building.

Using daylight and overheating as key design constraints, the tool provides simplified performance estimates informed by Passive House thermal comfort principles, including the guideline that indoor temperatures should not exceed 25°C for more than 10% of annual hours. Rather than replacing detailed energy simulation, the tool enables designers to understand the dynamic relationship between façade design, building massing, daylight, and thermal performance throughout the design process, supporting continuous design iteration.

## 3. Source (user, 2026-10-02)

- Passive House Institute China, “Passive House Requirements”, https://phichina.com/passive-house-requirements.html (accessed 2026-10-02; the page carries no version or date).
  Clause used: item 4, Thermal comfort — “not more than 10 % of the hours in a given year over 25 °C”.
  The tool reports that share as “overheating”; 10 % is shown as the limit and 5 % as a recommended target (the 5 % target is the tool's own choice, not from this page).
- Daylight factor 3 % “sufficient” and all climate numbers come from the shared engine (wwr-engine.js) and the three Vancouver EPW files in Passivehouse_Tool/02_Data/EPW — these are the tool's own assumptions / data, not regulations.

## 4. Example

- Format: GIF (user's choice, 2026-10-02). Built from fresh captures of the English page plus the two Rhino renders; see screenshots/demo.gif.
