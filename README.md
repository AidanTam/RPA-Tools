# SLR Celest Resource Estimation Tools

A Streamlit web application providing a suite of resource geology tools for sample analysis, QA/QC, geostatistics, and data validation.

**Version 1.0.2**

### 🌐 Live App

**[rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app](https://rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app)**

Hosted on Streamlit Community Cloud — no install required. Access is protected by a passphrase. The app auto-updates whenever changes are pushed to the `main` branch.

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

Opens at `http://localhost:8501` by default. Stop the server with `Ctrl+C` in the terminal it's running in.

### Troubleshooting

- **Code changes not showing up**: editing files in `pyrpa/` (not the entry-point `rpa_tools.py`) won't hot-reload — Python caches imported modules. Fully stop the server (`Ctrl+C`, or kill any process still bound to port 8501) and relaunch.
- **Port already in use**: another Streamlit instance may still be running. Find and stop it, or launch on a different port with `python -m streamlit run pyrpa/UI/rpa_tools.py --server.port 8502`.
- **Missing packages** (e.g. `pygwalker`, `transforms3d`): re-run `pip install -r pyrpa/UI/requirements.txt`.

### Hosted Version

This app can also be deployed to [Streamlit Community Cloud](https://streamlit.io/cloud) for browser access with no local install — see [Deployment](#deployment) below.

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

## Deployment

This app is deployed at **[rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app](https://rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app)** on [Streamlit Community Cloud](https://share.streamlit.io) (free):

1. Push the repo to GitHub (already done — `AidanTam/RPA-Tools`).
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account and authorize Streamlit's GitHub app.
3. Click **New app**, select this repo and the `main` branch, and set the main file path to `pyrpa/UI/rpa_tools.py`.
4. Under **Advanced settings**, set the Python version to match local development if needed, and add any secrets (API keys, etc.) under **Secrets** — none are currently required.
5. Click **Deploy**. The app builds from `pyrpa/UI/requirements.txt` and is live at a `*.streamlit.app` URL within a few minutes.
6. Future pushes to `main` redeploy automatically.

> **Note:** Vercel does not support Streamlit — it only runs serverless functions and static sites, not the persistent WebSocket server Streamlit requires. Streamlit Community Cloud, Render, Railway, or a VM are the viable hosts.

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
