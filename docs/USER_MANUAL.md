# Celest Tools User Manual

**SLR Celest Resource Estimation Tools · v1.0.2**

A browser-based Streamlit app of 18 tools that take drillhole assays from the
lab through to a defensible resource estimate: QA/QC, validation, statistics,
capping, geostatistics and reconciliation. No install required.

> Also available as a Word document: [Celest-Tools-User-Manual.docx](Celest-Tools-User-Manual.docx).

---

## 1. How the tools fit together: the geologist's workflow

The toolkit mirrors the life of a resource estimation study. Data has to be
**trusted** before it can be **understood**, **treated**, and finally
**modelled**. The stages run in order, early stages gate the later ones, so a
failed standard or a bad merge is caught before it contaminates a grade estimate.

| # | Stage | Question it answers | Tools |
|---|-------|--------------------|-------|
| 1 | **Validate incoming lab data** | Does the database match the lab certificates? | Data Verification |
| 2 | **QA/QC the assays** | Are the assay numbers reliable? | Standards, Blanks, Duplicates, Check Assays, Z-Score |
| 3 | **Explore the data** | How does grade behave, by domain? | Sample Statistics, Box Plot, Scatter Plot, Width Plot, Contact Analysis |
| 4 | **Data density & classification** | How tightly is each domain sampled? | DDH Spacing, Thin DDH Spacing |
| 5 | **Treat outliers (capping)** | What top-cut, and at what cost? | Capping Analysis, Uncapped vs Capped |
| 6 | **Geostatistics / change of support** | How do point samples become block estimates? | Gammabar Plot |
| 7 | **Block model & reconciliation** | Does the model line up with reality? | Convert Rotations, Drill Hole Comparison |

---

## 2. Getting started

- **Access.** The app is gated by a single team **passphrase**. No individual
  accounts; anyone with the link and passphrase can use every tool.
- **Two ways to load a file.** Drag & drop / browse via the sidebar uploader,
  or **"…or select from folder"** to pick a file already in the app's working
  directory.
- **Save this build.** **⬇ Download this version** zips the exact running
  codebase so you keep a working local copy.
- **Reruns.** Streamlit re-runs the whole script on every input change; a brief
  flash as charts rebuild is normal.
- **Navigation.** Pick a section in the sidebar, click a tool to open it,
  **← Back** to return to the section menu.

---

## 3. File input types

| Format | Extension | Accepted by | Notes |
|--------|-----------|-------------|-------|
| **CSV** | `.csv` | Every tool | Universal format; export from Excel or Datamine. |
| **Datamine** | `.dm` | Plotting, Sample, Geostats, Block model | Native Datamine data files, read directly, no export step. |
| **Excel** | `.xlsx`, `.xls` | All QA/QC tools; Data Verification (`.xlsx`/`.xlsm`) | Read straight from the workbook, lab certificates usually arrive as Excel. |
| **Config** | `.json` | QA/QC tools | Saves column mapping + filters. *Download config JSON* / *Load config*. |
| **Settings** | folder file | Capping, Statistics, Contact, DDH Spacing | *Load Settings* recalls a saved parameter preset. |

### The tools meet messy files halfway

- **Automatic column mapping.** QA/QC tools guess which column is Lab / Element
  / Value / Date / Unit / CRM / Expected Value / SD, tolerant of case and
  spacing (`Analyte` → Element, `Assay_Result` → Value, `certified value` →
  Expected). Override any guess manually.
- **Wide → long reshape.** A file with one column block per element (`Au_EV`,
  `Au_SD`, `Au_or_ppm`, `Ag_EV`, …) triggers a sidebar prompt to reshape it into
  the long Element/Value format the tools expect.
- **Detection-limit conversion** (Data Verification), `<0.5` becomes half the
  limit (0.25), `>10000` becomes the limit, so censored values compare
  arithmetically.
- **Field guessing.** Sample tools recognise `X/Y/Z`, `EAST/NORTH/ELEV`,
  `BHID`, `HOLEID`, `LENGTH`, `ZONE/DOMAIN/ROCK` on sight.

---

## 4. Tool reference

Grouped exactly as in the sidebar. *Mapped fields* are columns you select from
your file.

### Plotting Tools

| Tool | Purpose | Map | Output |
|------|---------|-----|--------|
| **Box Plot** | Grade distribution as box plots by domain/subdomain | Grade, Domain, (Subdomain); log option | Interactive chart |
| **Scatter Plot** | Bivariate relationship between two variables | Variable 1 & 2, colour-by, size-by, hover fields; log axes, marginals, colour scale | Interactive chart |
| **Width Plot** | Variable-width bar chart (width & height each field-driven) | Width, Height, Labels; sort by height | Interactive chart |

### Sample Tools

| Tool | Purpose | Map | Output |
|------|---------|-----|--------|
| **Statistics** | Descriptive stats per domain, weighted or unweighted | Grade Fields (many), Domain, Weight; invalid-number handling | Statistics table |
| **Capping Analysis** | Choose grade top-cut and read its impact (5 linked views) | Grade + unit (g/t, %, ppm, ppb, oz/t…), XYZ, Domain filter, Weight | Capping levels + metal-loss summary |
| **Uncapped vs Capped Plot** | Grade distribution before vs after capping | Uncapped, Capped, Domain, Weight; sort order | Comparison chart |
| **Contact Analysis** | Grade profile across a rock-type boundary (hard/soft/transitional) | Grade, XYZ, Domain, Rock 1, Rock 2 | Contact plot |
| **DDH Spacing** | Nearest-neighbour drillhole spacing per domain | Hole ID, XYZ, Domain | Spacing stats + plot |
| **Thin DDH Spacing** | Spacing tuned for thin/narrow-vein samples | Hole ID, XYZ | Spacing analysis |

**Capping Analysis views:** Summary · 3D · Orthogonal data view · Decile
Analysis · Log-Probability plot · Histogram.

### Block Model Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Convert Rotations** | Convert block-model rotation angles between software conventions | Angles + source/target convention | Converted angles |

### Geostats Tools

| Tool | Purpose | Set | Output |
|------|---------|-----|--------|
| **Gammabar Plot** | GSLIB gammabar (mean variogram over a block) for change-of-support; GSLIB rotation conventions | Block discretisation X/Y/Z, rotations, nugget, structures (type, sill C, ranges) | Gammabar plot |

### QA/QC

All five share a rhythm: upload CSV/Excel → confirm auto-mapped columns → filter
labs/elements → **Run** → export. Each produces an on-screen summary plus
downloadable **Excel** and **PowerPoint** reports, and can save its setup as a
config JSON.

| Tool | Purpose | Map |
|------|---------|-----|
| **Standards (CRM)** | Control charts of measured grade vs a reference material's certified value ± SD, per element over time | Date, Grade, CRM, Element, Expected Value, Project, Lab, Unit, SD/limit cols; failure criteria EV ± 1/2/3 SD |
| **Blanks** | Blank-sample contamination check vs an LOD-based floor | Lab, Element, Value, Date, Unit, LOD/DL, Blank-type; limits by constant or factor × LOD |
| **Duplicates** | Precision of duplicate pairs, Thompson-Howarth, scatter, HARD | Lab, Duplicate-type, Element, Unit, Original & Duplicate values, Date |
| **Check Assays** | Primary vs secondary (umpire) lab comparison | Primary-lab, Secondary-lab, Element, Original & Duplicate assay, Unit, Type, Date |
| **Z-Score** | Standardised z-score of standards over time (distance-from-expected in SD units) | Element, CRM, Value, Expected, SD, Date, Company |

### Data Validation

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **Data Verification** | Merge many lab certificates and reconcile them against the assay database, flagging mismatches | Certificates `.csv/.xlsx/.xlsm` (multiple) + assay database file | Merged CSV, per-element verification CSV, difference report |
| **Drill Hole Comparison** | Nearest-neighbour comparison of two datasets (e.g. blast holes vs drill holes) for reconciliation | Dataset 1 & 2 `.csv`; grade/length/coordinate/ID fields; capping values; one-to-one; distance threshold | Descriptive stats, histograms, CSV |

---

*Generated as a companion to the running app. Keep it in sync with
`pyrpa/UI/` when tools change.*
