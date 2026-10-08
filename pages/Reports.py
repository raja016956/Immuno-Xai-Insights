import streamlit as st
import json
from pathlib import Path
from utils.style import apply_style


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reports | ImmunoXAI",
    layout="wide"
)


# ============================================================
# PAGE STYLING
# ============================================================
apply_style()



# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<h1 class="glow-text">Reports</h1>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style="color:#94a3b8;">
        View your previous ImmunoXAI analysis reports and
        AI-generated biological interpretations.
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# REPORT STORAGE LOCATION
# ============================================================

# Reports will be stored in:
# project_folder/reports_data/reports_history.json

REPORT_FILE = (
    Path(__file__).resolve().parent.parent
    / "reports_data"
    / "reports_history.json"
)


# ============================================================
# LOAD REPORT HISTORY
# ============================================================

def load_reports():
    """
    Load previously generated reports.

    Returns:
        A list of reports sorted from newest to oldest.
    """

    # No report file means there are no reports yet
    if not REPORT_FILE.exists():
        return []

    try:

        with open(
            REPORT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reports = json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []

    # Newest report first
    reports.sort(
        key=lambda report: report.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    return reports


# ============================================================
# GET REPORTS
# ============================================================

reports = load_reports()


# ============================================================
# EMPTY STATE
# ============================================================

if not reports:

    st.info(
        "No analysis reports have been generated yet."
    )

else:

    # --------------------------------------------------------
    # History heading
    # --------------------------------------------------------

    st.markdown(
        '<h2 style="color:#40e0d0; margin-top:30px;">'
        'Analysis History'
        '</h2>',
        unsafe_allow_html=True
    )

# ============================================================
# ANALYSIS HISTORY
# ============================================================

from pathlib import Path
import json
from datetime import datetime

st.markdown(
    '<p style="color:#94a3b8;">'
    'View your previous ImmunoXAI analysis reports and '
    'AI-generated biological interpretations.'
    '</p>',
    unsafe_allow_html=True
)

# Location of saved reports
REPORT_FILE = (
    Path(__file__).resolve().parent.parent
    / "reports_data"
    / "reports_history.json"
)

# Load saved reports
reports = []

if REPORT_FILE.exists():
    try:
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            reports = json.load(f)

        if not isinstance(reports, list):
            reports = []

    except Exception:
        reports = []


# Show newest reports first
reports.sort(
    key=lambda x: x.get("created_at", ""),
    reverse=True
)


if not reports:

    with st.container(border=True, key="no_reports"):
        st.info("No analysis reports have been generated yet.")

else:

    for report_index, report in enumerate(reports):

        dataset_name = report.get(
            "dataset_name",
            "Unnamed Dataset"
        )

        created_at = report.get(
            "created_at",
            ""
        )

        # Format timestamp
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                formatted_time = dt.strftime(
                    "%d %b %Y, %I:%M %p"
                )
            except Exception:
                formatted_time = created_at
        else:
            formatted_time = "Unknown time"

        # Correct saved fields
        cells = report.get("cells", 0)
        inflamed = report.get("inflamed", 0)
        immune_excluded = report.get(
            "immune_excluded",
            0
        )

        accuracy = report.get(
            "accuracy",
            0
        )

        precision = report.get(
            "precision",
            0
        )

        recall = report.get(
            "recall",
            0
        )

        f1_score = report.get(
            "f1_score",
            0
        )

        ai_interpretation = report.get(
            "ai_interpretation",
            ""
        )

        # --------------------------------------------------------
        # REPORT CARD
        # --------------------------------------------------------

        with st.container(border=True,key=f"report_card_{report_index}"):

            st.markdown(
                f"""
                <h3 style="
                    color:#e2e8f0;
                    margin:0;
                ">
                    {dataset_name}
                </h3>

                <p style="
                    color:#64748b;
                    margin:4px 0 18px 0;
                    font-size:0.85rem;
                ">
                    Analysis completed: {formatted_time}
                </p>
                """,
                unsafe_allow_html=True
            )

            # Main statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Cells",
                    f"{cells:,}"
                )

            with col2:
                st.metric(
                    "Inflamed",
                    f"{inflamed:,}"
                )

            with col3:
                st.metric(
                    "Immune-Excluded",
                    f"{immune_excluded:,}"
                )

            with col4:
                st.metric(
                    "Accuracy",
                    f"{accuracy:.3f}"
                )

            # ----------------------------------------------------
            # Additional model metrics
            # ----------------------------------------------------

            st.markdown(
                "### Model Performance"
            )

           # ----------------------------------------------------
            # Additional model metrics
            # ----------------------------------------------------

            metric1, metric2, metric3, metric4 = st.columns(4)

            with metric1:
                st.metric(
                    "Precision",
                    f"{precision:.3f}"
                )

            with metric2:
                st.metric(
                    "Recall",
                    f"{recall:.3f}"
                )

            with metric3:
                st.metric(
                    "F1 Score",
                    f"{f1_score:.3f}"
                )

            with metric4:
                st.empty()

            # ----------------------------------------------------
            # AI interpretation
            # ----------------------------------------------------

            st.markdown(
                "### AI Biological Interpretation"
            )

            if ai_interpretation:

                with st.container(border=True,key=f"ai_interpretation_{report_index}"):
                    st.markdown(
                        ai_interpretation
                    )

            else:

                st.warning(
                    "AI interpretation is not available for this analysis."
                )

            # ----------------------------------------------------
            # Detailed analysis
            # ----------------------------------------------------

            with st.expander("View analysis details"):

                feature_importance = report.get(
                    "feature_importance",
                    []
                )

                if feature_importance:

                    st.markdown(
                        "### Important Genes"
                    )

                    st.dataframe(
                        feature_importance,
                        use_container_width=True,
                        hide_index=True
                    )