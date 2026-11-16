# Variable Site Framework — Thesis Site Research Brief

**Status:** Working research brief / current direction as of 2026-11-15  
**Course context:** ARCH 548 — Assignment 5: The Site & Program; related ARCH 540 computational-design research  
**Purpose:** Bring Claude Code up to date before starting Vancouver Open Data research.  
**Authority:** Summarizes decisions made in the user–ChatGPT site discussion and a 2.5-minute user–Joyce discussion. It is **not** a finalized software specification, a verified empirical finding, or permission to modify existing tools.

> **Central site proposition:** The thesis site is **not a single fixed geographic parcel**. It is a **Variable Site Framework**: a population of configurable, physically intelligible public open-space conditions derived from recurring characteristics of real Vancouver sites. The framework is a research input for a transferable winter semi-outdoor design methodology, **not** a predesigned architectural solution.

## 1. Thesis context and scope

Working thesis statement from earlier research:

> *Conditioned space can be reinterpreted as a calibrated gradient between climatic protection and environmental exposure, supporting year-round public occupation in Vancouver.*

**Current study scope is narrower than the general statement:**
- **Geographic/climate context:** Vancouver, British Columbia.
- **Focus:** Winter, **11:00 AM–3:00 PM**, a four-hour daytime analysis window.
- **Question:** How can an architectural design methodology match **Climate × Space × Activity** to enable public occupation without automatically providing uniformly or excessively conditioned environments?
- **Intended architectural outcome:** A **public-space system composed of multiple interconnected spatial prototypes**, whose specific forms emerge *later* from activity/environment matching, not from the site selection process.
- **Transferable output:** A design logic / guideline potentially applicable to many Vancouver outdoor and semi-outdoor public-space contexts. Joyce suggested framing the eventual thesis as a **design guidebook**; the exact final deliverable is still a proposition, not a fixed requirement.
- **Claims about reduced energy/conditioning need verification:** Matching activities to microclimates may reduce unnecessary conditioning; **energy or carbon reductions are not yet demonstrated**. PET alone does not measure rain protection, overall suitability, or energy use.

## 2. Separate the stages: Site is not Prototype

1. **SITE — existing or constructed base conditions:** geometry, boundaries, surroundings, topography, public connections, solar access, and exposure *before* design intervention.
2. **PROGRAM — human/activity requirements:** public activity types, activity intensity (MET), clothing (CLO), duration, thermal and nonthermal requirements.
3. **MATCHING / DESIGN METHOD:** compare program needs against winter site microclimates, identify conflicts and opportunities.
4. **ARCHITECTURAL RESPONSE:** only then develop spatial interventions, multiple connected prototypes, and a legible public-space system.

**Do not pre-place roofs, winter rooms, canopies, or a fixed number of prototypes inside the site definition.** The site may contain real surrounding buildings or vegetation as existing context; those are different from new thesis interventions.

## 3. Why a Variable Site?

Two complementary purposes:

- **Testing ground:** present meaningful combinations of climatic and spatial constraints against which the thesis method can be evaluated.
- **Explanatory framework:** make the relationships among climate, space, and public activity understandable through legible site conditions.
- **Comparative framework (proposed extension):** permit comparable cases / baselines and evaluation of alternative design responses.

A completely blank, homogeneous field is too abstract; a highly complex one-off site may hide the design logic. Seek **moderate, interpretable complexity**.

Initial site character: **relatively open and climatically exposed public ground**, with **partial urban enclosure**, a contrasting **open edge** (e.g. green space, waterfront, infrastructure), and connecting public ground. These are **starting hypotheses**, not mandatory characteristics for every site.

## 4. Foundational spatial ideas — open to revision

These three ideas are the **starting conceptual lenses**, **not** a closed list, a preset site typology, or three equivalent land-use categories:

| Initial lens | Guiding question | Possible measurable attributes (hypotheses, not verified standards) |
| --- | --- | --- |
| **Urban Edge** | How do surrounding buildings shape the site and its microclimate? | Nearby building footprints, heights, setbacks, urban frontage coverage, facade orientation, street/open-space H/W ratio where properly defined |
| **Open Edge** | What is the relationship to waterfront, parks, tree cover, other open land, or infrastructure? | Open-boundary type and length, aspect/orientation, distance to open space, vegetation or obstacle condition |
| **Public Ground** | How does the publicly usable ground between edges operate? | Ground polygon, area, aspect ratio, slope, entrances, connections, public accessibility, ground cover |

**Additional characteristics must be discoverable.** Examples to investigate rather than assume: intersection/corner conditions, discontinuous edges, passageways, variable height profiles, setback gradients, permeability, landscape/terrain edge, tree canopy, pedestrian paths, and orientation. Distinguish structural site attributes from outcomes produced by climatic simulation.

## 5. What is meant by “100 sites”?

- **Site population:** approximately **100 synthetic site configurations** generated from empirically grounded characteristic definitions, ranges, dependencies, and combinations. The number is a **working target, not a statistical guarantee**.
- **Real reference samples:** a separate collection of actual Vancouver spaces used to learn and verify characteristics, not necessarily 100 real sites.
- **Representative test sites:** a smaller subset chosen to stress-test and communicate the architectural methodology; do not design 100 complete buildings.

**Proposed hybrid pipeline:**

Real Vancouver examples → structured GIS/visual/field observations → AI-assisted characteristic discovery → precise parameter definitions + validity constraints → parameterized synthetic site population (~100) → baseline winter environmental assessment → representative site selection → later program/environment matching and architectural interventions.

Avoid naïvely combining independent averages or generating visually varied but implausible sites. Preserve real-world geometric dependencies and make assumptions explicit.

## 6. Site characteristic levels

| Level | Role | Example |
| --- | --- | --- |
| **A. Eligibility / scope** | Defines a candidate pool | Publicly accessible or genuinely public-facing ground; outdoor exposure; urban context. Record intervention potential without automatically excluding cases based on speculative permissions. |
| **B. Geometry / morphology** | Measured inputs for site generation | Polygon shape, orientation, edge length and proportions, adjacent buildings, height, setback, topography, vegetation |
| **C. Relationships / topology** | Explains how attributes interact | Building–ground distance, degree of enclosure, adjacency of parks or water, pedestrian connection, clustered obstructions |
| **D. Environmental performance** | Simulated/measured outputs, **not interchangeable with geometric inputs** | Sky View Factor (SVF), winter direct sun hours, incident radiation, pedestrian wind conditions, mean radiant temperature (MRT), PET, rain exposure |

A parameter registry should record: **name, operational definition, unit, data source & vintage, extraction method, assumptions, uncertainty, sample evidence, relevance to winter microclimate, and relevance to architecture**.

**Do not infer** accurate building height from a 2D footprint, public accessibility from parcel polygons or zoning alone, pedestrian wind speed from open-edge direction alone, or PET from shape/SVF alone. Rain and public access require distinct considerations. For hourly comparisons keep the same weather inputs and clearly document dates/weather scenarios, sun positions, and model assumptions within 11:00–15:00.

## 7. Proposed research and sampling protocol

### Stage 0 — Data feasibility (next immediate task)

Read the existing repository first; inspect City of Vancouver Open Data / VanMap sources and APIs. Inventory geometry, coverage, vintage, availability, format, API restrictions, licensing, and missing fields. **Read-only; no coding/writing yet.**

Candidate layers to investigate, not a claim that they are all complete or directly compatible:
- Parks and public/open-space boundaries
- Property parcel polygons
- Building footprints and building-height / LiDAR data
- Streets, paths and possible pedestrian connections
- Public trees / vegetation
- Terrain/topography
- Water boundaries and other open edges
- Community facility grounds or public plazas where authoritative data exists

Existing repo references:
- `Unprotected_Opening_Tool/` contains earlier Vancouver parcel/zoning/map prototypes and GIS querying.
- `Assignment_2/03_Data/` contains local-area boundary GeoJSON and climate-data handling material.
- `Assignment_2/01_Research/` includes thermal comfort, PET/UTCI, Vancouver climate, and program research.
- `Assignment_2/Tool_Logic_Draft_v2.md` describes an **earlier community-centre massing/program tool**. Some methods are reusable; its program, massing and five-stage design decisions **must not silently become fixed requirements for Variable Site**.
- Follow root `CLAUDE.md`; preserve existing folders, working demos, and `WORK_LOG.md`.

### Stage 1 — Broad exploratory candidate discovery

- Start from **public open spaces across Vancouver**, not only locations fitting all three initial lenses.
- Preliminary candidate types for coverage: urban plazas, community-facility grounds, park–urban interfaces, waterfront spaces, and infrastructure-adjacent open ground.
- Use spatial overlay and candidate polygon delineation; **parcel polygons are not synonymous with usable public grounds**.
- Proposed working scale: **30–50 candidates**, revised based on real coverage/data quality.
- Record source IDs and whether each candidate/site boundary was inferred, manually traced, or based on an authoritative polygon.

### Stage 2 — Pilot diversity sample

- Select ~**10–15 real reference sites** for deeper analysis.
- **Do not choose merely the “top” scored sites**; seek diversity of combinations, typical cases, edge cases, and some counterexamples to starting hypotheses.
- For each: site plan, contextual edge classification, measured geometry, available public-use evidence, data provenance, and a short list of potential climatic mechanisms to test.
- Keep observation, measured fact, AI hypothesis, and simulated result separately labeled.

### Stage 3 — Learn the characteristics

AI proposes recurring and unexpected attributes and relationships from structured evidence, not from unsupported visual impression. GIS/geometry code performs measurable calculations. Human researcher checks the architectural relevance and adjusts definitions.

Evaluate candidate characteristics using:
1. **Recurrence / distribution** (not merely most frequent)
2. **Winter climatic relevance** (testable causal or correlated mechanism)
3. **Architectural/design relevance**
4. **Measurability, reliability, and uncertainty**
5. **Coverage and distinctiveness** across the site population

### Stage 4 — Construct & validate synthetic sites

Establish conditional parameter ranges and legal/physical geometric constraints, then generate a stratified or otherwise coverage-oriented sample of ~100 plausible configurations. Check that the resulting population covers different site conditions and that synthetic configurations resemble plausible urban relations. Avoid claiming that a sample of 100 represents the statistical distribution of all Vancouver sites without evidence.

Assess the baseline environment **before** intervention, starting with feasible measures (solar, SVF) and escalating to appropriate wind/MRT/PET methods. Select representative cases for subsequent program–environment matching.

## 8. Assignment 5 — how this becomes a legible “site”

The ARCH 548 Assignment 5 brief accepts nontraditional / nongeographic sites or correlatives **if explicitly identified, documented, and analyzed**. It asks for site base documentation analogous to aerials, scaled plan, scaled sections and photos, plus **at least three conceptual site analytical images**; the program requires its own documentation and **at least three conceptual images**. Submission: letter-size PDF due **2026-11-18 at 12:00 PM**.

For the **Site** section, potential analytical images (proposals; do not imply simulations have already happened):
1. **Characteristic Extraction** — annotated Vancouver real-site examples and measurable shared/distinctive attributes.
2. **Variable Site Construction** — parameter definitions and spatial assembly diagrams; define what stays fixed vs varies.
3. **Site Population / Environmental Potential** — several contrasting valid configurations, with verified or clearly labeled hypothetical exposure implications.

The site correlative must still have a **readable physical shape** and spatial documentation. Do not substitute a purely abstract flowchart or a set of architectural prototypes for site plan/section.

## 9. Fixed vs variable vs open questions

**Currently fixed scope:** Vancouver winter; 11:00–15:00; public/open-ground context; comparative exposure conditions; site as a variable population; prototype generation is downstream.

**Initial variables to investigate:** building height and edge configuration; coverage and setbacks; open edge type and orientation; ground area/aspect/geometry; pathways/access; topography; vegetation; sky and wind exposure as modeled results.

**Still open:** exact definition of semi-public vs public and accessibility; real sample boundaries and sampling frame; actual dataset availability and ages; how many parameters and which must co-vary; whether base-ground size is fixed; how to represent site sections; acceptable environmental modeling fidelity; representative case selection; whether 100 is desirable after pilot testing.

## 10. Immediate instructions for Claude Code (read-only research)

**Before implementation or changes to GitHub**, perform a **Vancouver Open Data feasibility and site-characteristic discovery plan**.

Deliver findings **in the chat**, not by writing repository files:

1. Verified municipal datasets with official URL, currency/vintage, geometry type, license/API availability, and coverage.
2. Directly measurable attributes vs attributes needing merged datasets vs inaccessible/missing attributes.
3. Review of existing repo map/GIS components that could be reused **without modifying them**.
4. A reproducible pipeline for identifying 30–50 plausible candidates and selecting 10–15 diverse pilot cases.
5. Proposed **Site Characteristic Registry** with method and uncertainty for every attribute.
6. A minimal proposed first geographic test window and why it is suitable.
7. Technical/academic risks and the next choices requiring user approval.

**Never invent measurements, standards or dataset fields. Cite sources, distinguish verified facts from hypotheses, and do not write code or change files until explicitly instructed.**

## 11. Collaboration and versioning

This document is a living research brief for **ChatGPT ↔ GitHub ↔ Claude Code**, but **does not replace `CLAUDE.md` or other earlier project records**. Future changes should explicitly distinguish confirmed user decisions, suggestions from Joyce, AI proposals, and verified evidence. Follow existing repo conventions; do not reorganize prior tools or create a second work log.

**Source provenance:** site-design discussion in ChatGPT, Joyce discussion recording (“Site discussion - Variable Site,” 2026-11), and previously viewed ARCH 548 Assignment 5 handout. This file is a synthesis of the discussion, not a literal transcript.