# SLR Celest Resource Estimation Tools

A Streamlit web application providing a suite of resource geology tools for sample analysis, QA/QC, geostatistics, and data validation.

**Version 1.0.2**

---

## Getting Started

### Installation

```bash
git clone https://github.com/AidanTam/RPA-Tools.git
cd RPA-Tools
pip install -r pyrpa/UI/requirements.txt
```

### Running the App

```bash
python -m streamlit run pyrpa/UI/rpa_tools.py
```

Opens at `http://localhost:8501` by default.

---

## Tools

Select a section from the sidebar to browse available tools.

### Plotting Tools
| Tool | Description |
|------|-------------|
| Box Plot | Interactive box plots by domain and subdomain |
| Scatter Plot | Bivariate scatter plots with optional colour and size fields |
| Width Plot | Variable-width bar charts |

### Sample Tools
| Tool | Description |
|------|-------------|
| Statistics | Weighted/unweighted sample statistics by domain |
| Capping Analysis | Interactive capping level selection with spatial and histogram views |
| Uncapped vs Capped Plot | Side-by-side comparison of grade distributions before and after capping |
| Contact Analysis | Contact plots to assess hard/soft/transitional boundaries between domains |
| Calculate DDH Spacing | Nearest-neighbour drillhole spacing by domain |
| Thin DDH Spacing | Thin-sample drillhole spacing analysis |

### Block Model Tools
| Tool | Description |
|------|-------------|
| Convert Rotations | Convert rotation angles between block model conventions |

### Geostats Tools
| Tool | Description |
|------|-------------|
| Gammabar Plot | Gammabar variogram plot for change-of-support analysis |

### QA/QC
| Tool | Description |
|------|-------------|
| Standards | CRM/standard recovery charts and statistics |
| Blanks | Blank sample performance analysis |
| Duplicates | Duplicate pair analysis (Thompson-Howarth, scatter, HARD) |
| Check Assays | Check assay comparison plots |
| Z-Score | Z-score analysis for outlier detection |

### Data Validation
| Tool | Description |
|------|-------------|
| Data Verification Tool | Merge lab certificate files, compare against assay database |
| Drill Hole Comparison | Nearest-neighbour drillhole comparison |

---

## File Input

All tools that accept data files support two input methods:

- **Drag and drop / browse** — upload a `.csv` or `.dm` (Datamine) file directly via the sidebar uploader
- **Select from folder** — pick a file already in the working directory from the dropdown

---

## Dependencies

| Package | Version |
|---------|---------|
| streamlit | 1.23.1 |
| pandas | 1.4.2 |
| numpy | 1.22.4 |
| plotly | 5.8.2 |
| matplotlib | 3.5.2 |
| Pillow | 9.5.0 |
| transforms3d | 0.4.2 |
| pygwalker | 0.5.0.1 |
| pyrpa | 0.0.5 |

---

## Project Structure

```
RPA-Tools/
├── pyrpa/
│   ├── UI/
│   │   ├── rpa_tools.py          # App entry point
│   │   ├── common.py             # Shared widgets and file utilities
│   │   ├── capping_ui_v2.py
│   │   ├── sample_stats_ui.py
│   │   ├── ...                   # One *_ui.py per tool
│   │   └── requirements.txt
│   ├── capping.py
│   ├── sample.py
│   ├── contact_plot.py
│   └── ...                       # Backend computation modules
```
---

## Recent Improvements

| Module | Improvement |
|--------|-------------|
| Blanks | Y-axis limits can now be adjusted for blank values in the plot (Custom Y-limits in the Style options) |
| Standards (CRMs) | Automatic detection of header columns (Date, Grade, CRM, Element, Expected Value, Project, Lab, Unit) |
| Standards (CRMs) | Renamed fields: `Categorical column` → `Project`, `Optional Grouping Field 1` → `Lab` |
| Standards (CRMs) | `Unit` is now a trackable, auto-detected column (read per-chart) with a free-text fallback, instead of a fixed predefined list |
| Standards (CRMs) | Removed the upper/lower limit parameters from the combined CRM summary table |
| Capping | `Metal Loss` in the Capping Summary table now matches the `Percent Metal Loss` in the Decile Analysis table (computed from unrounded weighted averages) |
| Capping | Fixed the Capping Summary table rendering as all-NaN under newer pandas (chained-assignment issue) |

## Planned / Outstanding Updates

| Module | Update | Notes |
|--------|--------|-------|
| Standards (CRMs) | Restore the "no grouping field" chart branch | When no grouping field is selected, no chart/summary currently renders ([CRMs_ui.py](pyrpa/UI/CRMs_ui.py) ~line 1193 is a stub). Partly masked now that `Lab` auto-detects and triggers the working grouped path. |
| Dependencies | Reconcile `requirements.txt` with the installed environment | Pinned versions (pandas 1.4.2, etc.) differ from the environment in use (pandas 3.x); watch for chained-assignment patterns elsewhere. |
