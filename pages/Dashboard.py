import streamlit as st
from streamlit_firebase_auth import FirebaseAuth
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from utils.style import apply_style

# 1. Page Configuration (Must be first)
st.set_page_config(page_title="ImmunoXAI", layout="wide", initial_sidebar_state="expanded")

# Apply gloabl styles and VANTA animated background
apply_style()


# # 2. Inject Custom CSS for Background and "Glassmorphism" Effects
# st.markdown(
#     """
#     <style>
#     /* Add a light, biological/network background image */
#     [data-testid="stAppViewContainer"] {
#         background-image: linear-gradient(rgba(10, 14, 23, 0.85), rgba(10, 14, 23, 0.95)), 
#                           url("https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?q=80&w=2893&auto=format&fit=crop");
#         background-size: cover;
#         background-position: center;
#         background-attachment: fixed;
#     }
    
#     /* Style the sidebar to match the dark theme */
#     [data-testid="stSidebar"] {
#         background-color: rgba(17, 24, 39, 0.7) !important;
#         backdrop-filter: blur(10px);
#         border-right: 1px solid rgba(64, 224, 208, 0.2);
#     }

#     /* Custom turquoise header */
#     .glow-text {
#         color: #40e0d0;
#         text-shadow: 0 0 10px rgba(64, 224, 208, 0.5);
#         font-weight: 600;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

st.markdown('<h1 class="glow-text">ImmunoXAI</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #94a3b8; font-size: 1.1rem; margin-top: -15px;">IMMUNOMICS PLATFORM</p>', unsafe_allow_html=True)




# 1. Initialize Firebase Auth-----------------------------------------------------------------
auth = FirebaseAuth({
    "apiKey": st.secrets["FIREBASE_API_KEY"],
    "authDomain": st.secrets["FIREBASE_AUTH_DOMAIN"],
    "projectId": st.secrets["FIREBASE_PROJECT_ID"],
    "storageBucket": st.secrets["FIREBASE_STORAGE_BUCKET"],
    "messagingSenderId": st.secrets["FIREBASE_MESSAGING_SENDER_ID"],
    "appId": st.secrets["FIREBASE_APP_ID"]
})

# 2. Check current session status------------------------------------------------------------
user = auth.check_session()

if user:
    # -------------------------------------------------------------
    # PROTECTED CONTENT (LOGGED-IN USERS ONLY)
    # -------------------------------------------------------------
    
    # Safely retrieve email or display fallback
    user_email = user.get("email", "User") if isinstance(user, dict) else getattr(user, "email", "User")
    display_name = user_email.split("@")[0].capitalize()
        
    st.sidebar.write(f"Logged in as: **{display_name}**")
    
    # Render logout button in sidebar----------------------------------------------------
    with st.sidebar:
        auth.logout_form()

    # Main dashboard content---------------------------------------------------------------
    header_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
    
    with header_col:
        st.write(f"### Welcome back, {display_name}!")
        st.write("Your previous datasets, analyses, and downloadable reports.")
        
    with button_col:
        # This button sits on the right side and navigates to the Analysis page
        if st.button("New Analysis⏏️", use_container_width=True):
            st.switch_page("pages/Analysis.py")

    
    # ============================================================
    # SUMMARY CARDS
    # ============================================================

    # Load saved report history for the card values
    from pathlib import Path
    import json

    REPORT_FILE = (
        Path(__file__).resolve().parent.parent
        / "reports_data"
        / "reports_history.json"
    )

    reports = []

    if REPORT_FILE.exists():
        try:
            with open(REPORT_FILE, "r", encoding="utf-8") as file:
                reports = json.load(file)

            if not isinstance(reports, list):
                reports = []

        except (json.JSONDecodeError, OSError):
            reports = []

    analysed_datasets = len(
        set(
            report.get("dataset_name", "")
            for report in reports
            if report.get("dataset_name")
        )
    )

    completed_analyses = len(reports)
    generated_reports = len(reports)


    col1, col2, col3 = st.columns(3)


    # ------------------------------------------------------------
    # Analysed Datasets
    # ------------------------------------------------------------

    with col1:
        with st.container(border=True, key="summary_card_1"):

            st.html(
                f"""
            <div style="
                display:flex;
                align-items:center;
                gap:14px;
                margin-bottom:8px;
            ">

                <svg xmlns="http://w3.org"
                    height="36px"
                    viewBox="0 -960 960 960"
                    width="36px"
                    fill="#4ade80">

                    <path d="M120-120v-80h80v80h-80Zm160 0v-240h80v240h-80Zm160 0v-400h80v400h-80Zm160 0v-560h80v560h-80Zm160 0v-720h80v720h-80ZM240-524l136-136 170 170 294-294-56-56-238 238-170-170-192 192 56 56Z"/>

                </svg>

                <div style="
                    font-size:2rem;
                    font-weight:600;
                    color:#f8fafc;
                ">
                    {analysed_datasets}
                </div>

            </div>
            """
            )

            st.subheader("Analysed Datasets")
            st.write("Unique datasets analysed")


    # ------------------------------------------------------------
    # Completed Analyses
    # ------------------------------------------------------------

    with col2:
        with st.container(border=True, key="summary_card_2"):

            st.html(
            f"""
        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            margin-bottom:8px;
        ">

            <svg xmlns="http://w3.org"
                height="36px"
                viewBox="0 0 24 24"
                width="36px"
                fill="none"
                stroke="#4ade80"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round">

                <path d="M6 3h12M8 3v5l-4.6 8.2C2.7 17.5 3.6 19 5.1 19h13.8c1.5 0 2.4-1.5 1.7-1.8L16 8V3M10 9h4"/>

            </svg>

            <div style="
                font-size:2rem;
                font-weight:600;
                color:#f8fafc;
            ">
                {completed_analyses}
            </div>

        </div>
        """
        )

            st.subheader("Completed Analyses")
            st.write("Completed dataset analyses")


    # ------------------------------------------------------------
    # Generated Reports
    # ------------------------------------------------------------

    with col3:
        with st.container(border=True, key="summary_card_3"):

            st.html(
                f"""
            <div style="
                display:flex;
                align-items:center;
                gap:14px;
                margin-bottom:8px;
            ">

                <svg xmlns="http://w3.org"
                    height="36px"
                    viewBox="0 -960 960 960"
                    width="36px"
                    fill="#4ade80">

                    <path d="M240-80q-33 0-56.5-23.5T160-160v-640q0-33 23.5-56.5T240-880h320l240 240v480q0 33-23.5 56.5T720-80H240Zm280-560v-160H240v640h480v-480H520ZM240-760v160-160 640-640Z"/>

                </svg>

                <div style="
                    font-size:2rem;
                    font-weight:600;
                    color:#f8fafc;
                ">
                    {generated_reports}
                </div>

            </div>
            """
            )

            st.subheader("Generated Reports")
            st.write("Reports available")
        
    #-----------------------Previously analysed datasets---------------

    st.subheader("Previously analysed datasets")

    # =============================================================
    # PREVIOUS ANALYSIS REPORTS
    # =============================================================

    # Import report-history utilities here so this section
    # remains completely inside the logged-in dashboard.
    from pathlib import Path
    import json

    # -------------------------------------------------------------
    # Location of saved analysis reports
    # -------------------------------------------------------------

    REPORT_FILE = (
        Path(__file__).resolve().parent.parent
        / "reports_data"
        / "reports_history.json"
    )

    # -------------------------------------------------------------
    # Load previous reports
    # -------------------------------------------------------------

    reports = []

    if REPORT_FILE.exists():

        try:

            with open(
                REPORT_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                reports = json.load(file)

            # Make sure the loaded data is actually a list
            if not isinstance(reports, list):
                reports = []

        except Exception:

            # If the history file cannot be read,
            # do not break the dashboard.
            reports = []

    # -------------------------------------------------------------
    # Newest report first
    # -------------------------------------------------------------

    reports.sort(
        key=lambda report: report.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    # =============================================================
    # REPORT HISTORY DISPLAY
    # =============================================================

    if reports:

        st.markdown(
            """
            <p style="
                color:#94a3b8;
                margin-top:-5px;
                margin-bottom:20px;
            ">
                Your latest completed ImmunoXAI analyses.
            </p>
            """,
            unsafe_allow_html=True
        )

        # ---------------------------------------------------------
        # Display every saved report
        # ---------------------------------------------------------

        for report in reports:

            # -----------------------------------------------------
            # Basic report information
            # -----------------------------------------------------

            dataset_name = report.get(
                "dataset_name",
                "Unknown Dataset"
            )

            created_at = report.get(
                "created_at",
                "Unknown date"
            )

            cells = report.get(
                "cells",
                "-"
            )

            inflamed = report.get(
                "inflamed",
                "-"
            )

            immune_excluded = report.get(
                "immune_excluded",
                "-"
            )

            accuracy = report.get(
                "accuracy"
            )

            # -----------------------------------------------------
            # Format model accuracy
            # -----------------------------------------------------

            if isinstance(
                accuracy,
                (int, float)
            ):

                accuracy_display = (
                    f"{accuracy * 100:.1f}%"
                )

            else:

                accuracy_display = "-"

            # -----------------------------------------------------
            # Report card
            # -----------------------------------------------------

            with st.container(border=True, key="report_history"):

                # Dataset name and date
                st.html(
                    f"""
                    <div style="
                        margin-bottom:15px;
                    ">
                        <h3 style="
                            color:#e2e8f0;
                            margin:0;
                            font-size:1.15rem;
                            font-weight:600;
                        ">
                            {dataset_name}
                        </h3>

                        <p style="
                            color:#64748b;
                            margin:4px 0 0 0;
                            font-size:0.85rem;
                        ">
                            Analysis completed: {created_at}
                        </p>
                    </div>
                    """
                )

                # -------------------------------------------------
                # Analysis summary cards
                # -------------------------------------------------

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Cells / Samples",
                        f"{cells:,}"
                        if isinstance(
                            cells,
                            int
                        )
                        else cells
                    )

                with col2:

                    st.metric(
                        "Inflamed",
                        f"{inflamed:,}"
                        if isinstance(
                            inflamed,
                            int
                        )
                        else inflamed
                    )

                with col3:

                    st.metric(
                        "Immune-Excluded",
                        f"{immune_excluded:,}"
                        if isinstance(
                            immune_excluded,
                            int
                        )
                        else immune_excluded
                    )

                with col4:

                    st.metric(
                        "Model Accuracy",
                        accuracy_display
                    )

                # -------------------------------------------------
                # Biological interpretation
                # -------------------------------------------------

                interpretation = report.get(
                    "ai_interpretation",
                    ""
                )

                if interpretation:

                    st.markdown(
                        """
                        <h4 style="
                            color:#40e0d0;
                            margin-top:20px;
                            margin-bottom:8px;
                        ">
                            Biological Interpretation
                        </h4>
                        """,
                        unsafe_allow_html=True
                    )

                    with st.container(border=True):

                        st.markdown(
                            interpretation
                        )

                # -------------------------------------------------
                # Additional report information
                # -------------------------------------------------

                with st.expander(
                    "View analysis details"
                ):

                    # Immune-state information
                    st.markdown(
                        "#### Immune-State Summary"
                    )

                    detail_col1, detail_col2 = st.columns(2)

                    with detail_col1:

                        st.write(
                            "**Inflamed cells:**",
                            inflamed
                        )

                    with detail_col2:

                        st.write(
                            "**Immune-Excluded cells:**",
                            immune_excluded
                        )

                    # -------------------------------------------------
                    # Optional metrics
                    # -------------------------------------------------

                    if "precision" in report:

                        st.write(
                            "**Precision:**",
                            f"{report['precision']:.3f}"
                            if isinstance(
                                report["precision"],
                                (int, float)
                            )
                            else report["precision"]
                        )

                    if "recall" in report:

                        st.write(
                            "**Recall:**",
                            f"{report['recall']:.3f}"
                            if isinstance(
                                report["recall"],
                                (int, float)
                            )
                            else report["recall"]
                        )

                    if "f1_score" in report:

                        st.write(
                            "**F1 Score:**",
                            f"{report['f1_score']:.3f}"
                            if isinstance(
                                report["f1_score"],
                                (int, float)
                            )
                            else report["f1_score"]
                        )

                    # -------------------------------------------------
                    # Feature importance table if available
                    # -------------------------------------------------

                    feature_importance = report.get(
                        "feature_importance"
                    )

                    if feature_importance:

                        st.markdown(
                            "#### Top Important Genes"
                        )

                        st.dataframe(
                            pd.DataFrame(
                                feature_importance
                            ),
                            use_container_width=True,
                            hide_index=True
                        )

    else:

        # =========================================================
        # NO REPORTS YET
        # =========================================================

        with st.container(border=True):

            st.markdown(
                """
                <div style="
                    text-align:center;
                    padding:30px 20px;
                ">

                    <h3 style="
                        color:#e2e8f0;
                        margin-bottom:8px;
                    ">
                        No previous analysis reports
                    </h3>

                    <p style="
                        color:#94a3b8;
                        margin:0;
                    ">
                        Run a dataset analysis to generate
                        your first ImmunoXAI report.
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )
  



else:
    # --------------------------------------------------------------------------------
    # PUBLIC CONTENT (LOGGED-OUT USERS)
    # -------------------------------------------------------------------------
    st.warning("Please log in to access the platform.")
    auth.login_form()
