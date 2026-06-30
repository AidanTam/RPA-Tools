import sys
import os
import runpy
import io
import zipfile
from importlib import reload
import streamlit as st
from PIL import Image

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

path = os.path.dirname(__file__)

# Ensure the repo root is importable regardless of working directory/mount
# layout (e.g. Streamlit Cloud doesn't put it on sys.path the way running
# locally from the repo root does), so `import pyrpa` resolves to the local
# package rather than failing or shadowing an unrelated PyPI package.
_repo_root = os.path.abspath(os.path.join(path, '..', '..'))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

st.set_page_config(page_title="SLR Celest RPA Tools", layout="wide")

# Suppress set_page_config in child tool modules — it can only be called once
import streamlit as _st
_st.set_page_config = lambda *args, **kwargs: None

# ── Passphrase gate ─────────────────────────────────────────────────────────
# Internal-tool access control. Set APP_PASSWORD in Streamlit secrets (or the
# APP_PASSWORD env var) to override the default; falls back to "SLR123".
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "SLR123")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("SLR Celest RPA Tools")
    passphrase = st.text_input("Enter passphrase to continue", type="password")
    if passphrase:
        if passphrase == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect passphrase.")
    st.stop()

logo = Image.open(os.path.join(path, 'logo-slr-2018.png'))
st.sidebar.image(logo, caption='')
logo = Image.open(os.path.join(path, 'Celest.png'))
st.sidebar.image(logo, caption='')


@st.cache_data(show_spinner=False)
def _build_repo_zip():
    """Zip up the currently-running codebase so users can keep a local
    copy that won't change if the hosted version is later updated/broken."""
    exclude_dirs = {'.git', '__pycache__', '.streamlit'}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(_repo_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                full = os.path.join(root, f)
                zf.write(full, os.path.relpath(full, _repo_root))
    return buf.getvalue()


st.sidebar.download_button(
    "⬇️ Download this version",
    data=_build_repo_zip(),
    file_name="RPA-Tools.zip",
    mime="application/zip",
    use_container_width=True,
    help="Download the codebase exactly as it's running right now, so you have a local copy to fall back on.",
)
st.sidebar.divider()

SECTIONS = ["Home", "Plotting Tools", "Sample Tools", "Block Model Tools", "Geostats Tools", "QA/QC", "Data Validation"]
section = st.sidebar.radio("", SECTIONS)

if 'active_tool' not in st.session_state:
    st.session_state.active_tool = None
if 'active_section' not in st.session_state:
    st.session_state.active_section = section

# Reset tool when the user switches sections
if section != st.session_state.active_section:
    st.session_state.active_tool = None
    st.session_state.active_section = section


def tool_button(label, module):
    if st.button(label, use_container_width=True):
        st.session_state.active_tool = module
        st.rerun()


def run_active_tool():
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.active_tool = None
            st.rerun()
    st.divider()
    module_path = os.path.join(path, st.session_state.active_tool)
    runpy.run_path(module_path, run_name='__main__')


# ── Home ─────────────────────────────────────────────────────────────────────
if section == "Home":
    st.session_state.active_tool = None
    st.title("SLR Celest Resource Estimation Tools")
    st.markdown("A collection of miraculous tools for resource geologists.")
    st.markdown("**Version 1.0.2**")
    st.markdown("Select a tool from the sidebar to get started.")
    image = Image.open(os.path.join(path, 'gibraltar_0857.jpg'))
    st.image(image, caption='', use_container_width=True)

# ── Plotting Tools ────────────────────────────────────────────────────────────
elif section == "Plotting Tools":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## Plotting Tools")
        tool_button("Box Plot",        "box_plot_ui.py")
        tool_button("Scatter Plot",    "scatter_plot_ui.py")
        tool_button("Width Plot",      "width_plot_ui.py")

# ── Sample Tools ──────────────────────────────────────────────────────────────
elif section == "Sample Tools":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## Sample Tools")
        tool_button("Statistics",             "sample_stats_ui.py")
        tool_button("Capping Analysis",       "capping_ui_v2.py")
        tool_button("Uncapped vs Capped Plot","capped_vs_uncapped_plot_ui.py")
        tool_button("Contact Analysis",       "contact_plot_ui.py")
        tool_button("Calculate DDH Spacing",  "ddh_spacing_ui.py")
        tool_button("Thin DDH Spacing",       "thin_ddh_spacing_ui.py")

# ── Block Model Tools ─────────────────────────────────────────────────────────
elif section == "Block Model Tools":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## Block Model Tools")
        if st.checkbox("Block Model Validation"):
            tool_button("Convert Rotations (between conventions)", "convert_rotation_ui.py")

# ── Geostats Tools ────────────────────────────────────────────────────────────
elif section == "Geostats Tools":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## Geostats Tools")
        tool_button("Gammabar Plot", "gammabar_ui.py")

# ── QA/QC ─────────────────────────────────────────────────────────────────────
elif section == "QA/QC":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## QA/QC Tools")
        tool_button("Standards",    "CRMs_ui.py")
        tool_button("Blanks",       "Blanks_ui.py")
        tool_button("Duplicates",   "Duplicates_ui_nuggets.py")
        tool_button("Check Assays", "Check_assay_ui.py")
        tool_button("Z-Score",      "Z_Score_ui.py")

# ── Data Validation ───────────────────────────────────────────────────────────
elif section == "Data Validation":
    if st.session_state.active_tool:
        run_active_tool()
    else:
        st.markdown("## Data Validation")
        tool_button("Data Verification Tool", "data_verification_ui.py")
        tool_button("Drill Hole Comparison",  "Get_Nearest_ui.py")
