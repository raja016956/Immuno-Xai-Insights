from xmlrpc import client
import pandas as pd
import streamlit as st
from pipeline import run_pipeline
import plotly.express as px
import os
from groq import Groq
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ============================================================
# ANALYSIS PAGE STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* Biological / network background */
    [data-testid="stAppViewContainer"] {
        background-image:
            linear-gradient(
                rgba(10, 14, 23, 0.85),
                rgba(10, 14, 23, 0.95)
            ),
            url("https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?q=80&w=2893&auto=format&fit=crop");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(17, 24, 39, 0.7) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(64, 224, 208, 0.2);
    }

    /* Main glowing headings */
    .glow-text {
        color: #40e0d0;
        text-shadow: 0 0 10px rgba(64, 224, 208, 0.5);
        font-weight: 600;
    }

    /* Start Analysis button */
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #40e0d0 !important;
        color: #0a0e17 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: 1px solid #40e0d0 !important;
        padding: 0.5rem 2rem !important;
        box-shadow: 0 0 10px rgba(64, 224, 208, 0.2) !important;
    }

    div.stButton > button[data-testid="stBaseButton-primary"]:hover {
        background-color: transparent !important;
        color: #40e0d0 !important;
        border: 1px solid #40e0d0 !important;
        box-shadow: 0 0 20px rgba(64, 224, 208, 0.5) !important;
    }

    /* Upload card */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
        border-radius: 10px !important;
        background-color: rgba(15, 23, 42, 0.35) !important;
        backdrop-filter: blur(8px);
    }

    </style>
    """,
    unsafe_allow_html=True
)



# ============================================================
# LOAD GROQ API KEY
# ============================================================

# Load the .env file from the project root
load_dotenv()

# Retrieve the API key securely from the environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============================================================
# GENERATE AI BIOLOGICAL INTERPRETATION
# ============================================================

def generate_ai_interpretation(adata):
    """
    Generate a concise biological interpretation from the
    completed computational analysis.

    Input:
        adata: Processed AnnData object containing immune
               scores, immune states, model results, and
               feature importance.

    Returns:
        A short LLM-generated interpretation.
    """

    # ------------------------------------------------------------
    # Get immune-state counts
    # ------------------------------------------------------------
    state_counts = adata.obs["Immune_State"].value_counts()

    immune_excluded = int(
        state_counts.get("Immune-Excluded", 0)
    )

    intermediate = int(
        state_counts.get("Intermediate", 0)
    )

    inflamed = int(
        state_counts.get("Inflamed", 0)
    )

    # ------------------------------------------------------------
    # Get mean immune scores
    # ------------------------------------------------------------
    tcell_mean = float(
        adata.obs["Tcell_score"].mean()
    )

    pdl1_mean = float(
        adata.obs["PDL1_myeloid_score"].mean()
    )

    isi_mean = float(
        adata.obs["Immune_State_Index"].mean()
    )

    # ------------------------------------------------------------
    # Get model performance
    # ------------------------------------------------------------
    evaluation = adata.uns.get(
        "model_evaluation",
        {}
    )

    accuracy = float(
        evaluation.get("accuracy", 0)
    )

    precision = float(
        evaluation.get("precision", 0)
    )

    recall = float(
        evaluation.get("recall", 0)
    )

    # Support either key used by the pipeline/report
    f1_score = float(
        evaluation.get(
            "f1_score",
            evaluation.get("f1", 0)
        )
    )

    # ------------------------------------------------------------
    # Get important genes
    # ------------------------------------------------------------
    feature_importance = adata.uns.get(
        "feature_importance"
    )

    important_genes = []

    if feature_importance is not None:

        for _, row in feature_importance.head(10).iterrows():

            direction = (
                "Inflamed"
                if float(row["Coefficient"]) > 0
                else "Immune-Excluded"
            )

            important_genes.append({
                "gene": str(row["Gene"]),
                "coefficient": round(
                    float(row["Coefficient"]), 4
                ),
                "importance": round(
                    float(row["Importance"]), 4
                ),
                "model_direction": direction
            })

    # ------------------------------------------------------------
    # Prepare analysis results for the LLM
    # ------------------------------------------------------------
    analysis_summary = {
        "dataset": {
            "cells": int(adata.n_obs),
            "genes": int(adata.n_vars)
        },

        "immune_states": {
            "immune_excluded": immune_excluded,
            "intermediate": intermediate,
            "inflamed": inflamed
        },

        "immune_scores": {
            "mean_tcell_score": tcell_mean,
            "mean_pdl1_myeloid_score": pdl1_mean,
            "mean_immune_state_index": isi_mean
        },

        "model_performance": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        },

        "top_important_genes": important_genes
    }

    # ------------------------------------------------------------
    # Instructions for the LLM
    # ------------------------------------------------------------
    system_prompt = """
You are a biomedical data interpretation assistant.

Interpret ONLY the computational results provided to you.

Generate a concise dashboard interpretation in 4 to 6
short bullet points.

Discuss:
1. The overall immune-state pattern.
2. The T-cell and PD-L1/myeloid score pattern.
3. The most important model features.
4. The classifier performance.
5. One important scientific limitation.

Rules:
- Do not invent genes, pathways, or results.
- Do not claim that a gene causes an immune state.
- Feature importance represents model association, not causation.
- Do not make clinical claims.
- Do not overstate the findings.
- Use clear scientific language.
"""

    # ------------------------------------------------------------
    # Send analysis results to Groq
    # ------------------------------------------------------------
    user_prompt = f"""
Interpret the following ImmunoXAI analysis results:

{json.dumps(analysis_summary, indent=2)}

Return ONLY 4 to 6 concise bullet points.
"""

    # ------------------------------------------------------------
    # Check API key
    # ------------------------------------------------------------
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY was not found in the .env file."
        )

    # ------------------------------------------------------------
    # Create Groq client
    # ------------------------------------------------------------
    client = Groq(
        api_key=GROQ_API_KEY
    )

    # ------------------------------------------------------------
    # Generate interpretation
    # ------------------------------------------------------------
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.5,
        max_completion_tokens=1000,
        reasoning_effort="low",
        include_reasoning=False
    )

    # ------------------------------------------------------------
    # Get final LLM response
    # ------------------------------------------------------------
    content = response.choices[0].message.content

    if content is None or not content.strip():
        raise RuntimeError(
            "Groq returned an empty AI interpretation."
        )

    return content.strip()
# ============================================================
# SAVE ANALYSIS REPORT
# ============================================================
def save_analysis_report(adata, dataset_name, ai_interpretation):
    """Save the completed analysis and AI interpretation to report history."""

    reports_dir = (
        Path(__file__).resolve().parent.parent / "reports_data"
    )
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_file = reports_dir / "reports_history.json"

    # Load existing reports
    if report_file.exists():
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                reports = json.load(f)

            if not isinstance(reports, list):
                reports = []

        except Exception:
            reports = []
    else:
        reports = []

    # Get model evaluation results
    model_evaluation = adata.uns.get("model_evaluation", {})

    # Get immune-state counts
    state_counts = (
        adata.obs["Immune_State"]
        .value_counts()
        .to_dict()
    )

    # Get feature importance
    feature_importance = adata.uns.get(
        "feature_importance",
        pd.DataFrame()
    )

    if isinstance(feature_importance, pd.DataFrame):
        feature_importance = feature_importance.to_dict(
            orient="records"
        )

    # Create report
    report = {
        "created_at": datetime.now().isoformat(),
        "dataset_name": dataset_name,

        "cells": int(adata.n_obs),

        "inflamed": int(
            state_counts.get("Inflamed", 0)
        ),

        "immune_excluded": int(
            state_counts.get("Immune-Excluded", 0)
        ),

        "accuracy": float(
            model_evaluation.get("accuracy", 0)
        ),

        "precision": float(
            model_evaluation.get("precision", 0)
        ),

        "recall": float(
            model_evaluation.get("recall", 0)
        ),

        "f1_score": float(
            model_evaluation.get("f1", 0)
        ),

        "ai_interpretation": ai_interpretation,

        "feature_importance": feature_importance
    }

    # Add newest report
    reports.append(report)

    # Newest first
    reports.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    # Save
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            reports,
            f,
            indent=4,
            ensure_ascii=False
        )



# ============================================================
# TEST GROQ CONNECTION
# ============================================================

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY was not found in the .env file."
    )
    st.stop()


# ============================================================
# ANALYSIS PAGE HEADER
# ============================================================

# st.markdown(
#     '<h1 style="color: red; ">Analysis</h1>',
#     unsafe_allow_html=True
# )

st.markdown(
    '<h1 class="glow-text">Analysis</h1>',
    unsafe_allow_html=True
)



st.markdown('<p style="color: #94a3b8; font-size: 1.1rem; margin-top: -15px;"> Run the complete ImmunoXAI single-cell analysis pipeline and generate an AI biological interpretation.</p>', unsafe_allow_html=True)

# ============================================================
# DATASET UPLOAD
# ============================================================

# SVG icons
svg_dataset = '''
<svg xmlns="http://www.w3.org/2000/svg"
width="24" height="24" viewBox="0 0 24 24"
fill="none" stroke="#40e0d0" stroke-width="2"
stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4A2 2 0 0 0 21 16z"/>
<polyline points="3.29 7 12 12 20.71 7"/>
<line x1="12" x2="12" y1="22" y2="12"/>
</svg>
'''

svg_cloud = '''
<svg xmlns="http://www.w3.org/2000/svg"
width="24" height="24" viewBox="0 0 24 24"
fill="none" stroke="#40e0d0" stroke-width="2"
stroke-linecap="round" stroke-linejoin="round">
<path d="M17.5 19H9a7 7 0 1 1 6.71-9H17.5a5.5 5.5 0 0 1 0 11z"/>
<polyline points="12 12 12 17"/>
<polyline points="9 15 12 12 15 15"/>
</svg>
'''

# Center the upload area
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:

    # Upload heading and description
    st.html(
        f"""
<div style="display:flex; align-items:flex-start; gap:16px; margin-bottom:20px;">

    <div style="
        background-color:rgba(64,224,208,0.10);
        padding:12px;
        border-radius:12px;
        display:flex;
        align-items:center;
        justify-content:center;">
        {svg_dataset}
    </div>

    <div>
        <h3 style="
            margin:0;
            color:#e2e8f0;
            font-size:1.2rem;
            font-weight:600;">
            Upload your dataset
        </h3>

        <p style="
            margin:4px 0 0 0;
            color:#94a3b8;
            font-size:0.95rem;
            line-height:1.4;">
            Upload a single-cell gene expression matrix.
            ImmunoXAI will validate the dataset and run the
            complete computational analysis pipeline.
        </p>
    </div>

</div>

<hr style="
    border:0;
    border-top:1px solid rgba(255,255,255,0.10);
    margin-bottom:24px;">
""",
    )

    # Transparent / light-black upload box
    with st.container(border=True):

        st.html(
            f"""
<div style="text-align:center; padding:20px 10px 10px 10px;">

    <div style="
        background-color:rgba(255,255,255,0.95);
        width:48px;
        height:48px;
        border-radius:12px;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        margin-bottom:16px;
        box-shadow:0 4px 6px rgba(0,0,0,0.15);">
        {svg_cloud}
    </div>

    <h4 style="
        margin:0 0 8px 0;
        color:#e2e8f0;
        font-size:1.1rem;
        font-weight:600;">
        Upload expression matrix
    </h4>

    <p style="
        margin:0 0 16px 0;
        color:#94a3b8;
        font-size:0.9rem;">
        CSV, TSV, TXT, or compressed GZ files
    </p>

</div>
""",
        )

        # Actual Streamlit uploader
        uploaded_file = st.file_uploader(
            "Upload expression matrix",
            type=["csv", "tsv", "txt", "gz"],
            label_visibility="collapsed"
        )


# ============================================================
# START ANALYSIS
# ============================================================

# Keep the button directly below the upload card
with col_center:

    st.markdown(
        '<div style="height: 12px;"></div>',
        unsafe_allow_html=True
    )

    start_analysis = st.button(
        "▶ Start Analysis",
        type="primary",
        disabled=(uploaded_file is None)
    )

    if start_analysis:

        try:

            # Run the complete computational pipeline
            with st.spinner(
                "Running ImmunoXAI analysis..."
            ):

                adata, inspection, verification = run_pipeline(
                    uploaded_file
                )

            # Save pipeline results
            st.session_state["adata"] = adata
            st.session_state["inspection"] = inspection
            st.session_state["verification"] = verification

            # Generate AI interpretation
            with st.spinner(
                "Generating AI biological interpretation..."
            ):

                ai_interpretation = generate_ai_interpretation(
                    adata
                )

            # Save AI interpretation
            st.session_state["ai_interpretation"] = (
                ai_interpretation
            )

            # Save report
            save_analysis_report(
                adata,
                uploaded_file.name,
                ai_interpretation
            )

            st.success(
                "Dataset analysis and AI interpretation "
                "completed successfully!"
            )

        except ValueError as e:

            st.error(str(e))

        except Exception as e:

            st.error(
                f"Analysis failed: {e}"
            )

# ============================================================
# PREPROCESSING VERIFICATION
# ============================================================

if "verification" in st.session_state:

    # Retrieve the verification results saved by the pipeline
    verification = st.session_state["verification"]

    # --------------------------------------------------------
    # Verification heading
    # --------------------------------------------------------
    st.markdown(
        '<h2 style="color: #40e0d0; margin-top: 30px;">'
        'Preprocessing Verification'
        '</h2>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Display the main verification statistics
    # --------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    # Number of cells/samples remaining
    with col1:
        st.metric(
            "Cells / Samples",
            verification["cells"]
        )

    # Number of genes remaining
    with col2:
        st.metric(
            "Genes",
            verification["genes"]
        )

    # Required immune-marker genes
    with col3:
        st.metric(
            "Required Genes",
            "Yes"
            if verification["required_genes_present"]
            else "No"
        )

    # --------------------------------------------------------
    # Check expression values
    # --------------------------------------------------------
    if not verification["contains_invalid_values"]:

        st.success(
            "✓ No NaN or infinite values were found "
            "after preprocessing."
        )

    else:

        st.error(
            "Invalid expression values were found "
            "after preprocessing."
        )
# ============================================================
# IMMUNE SCORE SUMMARY
# ============================================================

if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # --------------------------------------------------------
    # Check that immune scores were calculated
    # --------------------------------------------------------
    required_scores = [
        "Tcell_score",
        "PDL1_myeloid_score",
        "Immune_State_Index"
    ]

    missing_scores = [
        score
        for score in required_scores
        if score not in adata.obs.columns
    ]

    # Stop if the scoring stage did not create the columns
    if missing_scores:

        st.error(
            "Immune score columns are missing: "
            + ", ".join(missing_scores)
        )

    else:

        # ----------------------------------------------------
        # Display section heading
        # ----------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 30px;">'
            'Immune Score Summary'
            '</h2>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # Calculate summary statistics
        # ----------------------------------------------------
        tcell = adata.obs["Tcell_score"]
        pdl1 = adata.obs["PDL1_myeloid_score"]
        isi = adata.obs["Immune_State_Index"]

        # ----------------------------------------------------
        # Create three columns
        # ----------------------------------------------------
        col1, col2, col3 = st.columns(3)

        # ----------------------------------------------------
        # T-cell score
        # ----------------------------------------------------
        with col1:

            st.markdown("**T-cell Score**")

            st.metric(
                "Mean",
                f"{tcell.mean():.3f}"
            )

            st.write(
                f"Min: {tcell.min():.3f}"
            )

            st.write(
                f"Max: {tcell.max():.3f}"
            )

        # ----------------------------------------------------
        # PD-L1 / myeloid score
        # ----------------------------------------------------
        with col2:

            st.markdown("**PD-L1 / Myeloid Score**")

            st.metric(
                "Mean",
                f"{pdl1.mean():.3f}"
            )

            st.write(
                f"Min: {pdl1.min():.3f}"
            )

            st.write(
                f"Max: {pdl1.max():.3f}"
            )

        # ----------------------------------------------------
        # Immune State Index
        # ----------------------------------------------------
        with col3:

            st.markdown("**Immune State Index**")

            st.metric(
                "Mean",
                f"{isi.mean():.3f}"
            )

            st.write(
                f"Min: {isi.min():.3f}"
            )

            st.write(
                f"Max: {isi.max():.3f}"
            )
# ============================================================
# IMMUNE STATE INDEX THRESHOLDS
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Get the Immune State Index
    isi = adata.obs["Immune_State_Index"]

    # Calculate distribution thresholds
    q25 = float(isi.quantile(0.25))
    median = float(isi.quantile(0.50))
    q75 = float(isi.quantile(0.75))

    # ============================================================
    # CREATE IMMUNE STATE LABELS
    # ============================================================

    # Start all cells as Intermediate
    adata.obs["Immune_State"] = "Intermediate"

    # Lower 25% = Immune-Excluded
    adata.obs.loc[
        isi <= q25,
        "Immune_State"
    ] = "Immune-Excluded"

    # Upper 25% = Inflamed
    adata.obs.loc[
        isi >= q75,
        "Immune_State"
    ] = "Inflamed"

    # Calculate number of cells in each distribution range
    low_count = int((isi <= q25).sum())
    middle_count = int(((isi > q25) & (isi < q75)).sum())
    high_count = int((isi >= q75).sum())

    # --------------------------------------------------------
    # Display section heading
    # --------------------------------------------------------
    st.markdown(
        '<h2 style="color: #40e0d0; margin-top: 35px;">'
        'Immune State Thresholds'
        '</h2>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="color: #b8c7d9;">'
        'Distribution-based thresholds for the Immune State Index.'
        '</p>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Display Q25, Median, and Q75
    # --------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Q25",
            f"{q25:.3f}"
        )

    with col2:
        st.metric(
            "Median",
            f"{median:.3f}"
        )

    with col3:
        st.metric(
            "Q75",
            f"{q75:.3f}"
        )

    # --------------------------------------------------------
    # Display distribution counts
    # --------------------------------------------------------
    st.markdown(
        f"""
        <div style="
            margin-top: 15px;
            padding: 12px 18px;
            border-radius: 10px;
            background: rgba(15, 23, 42, 0.70);
            color: #b8c7d9;
        ">
            <b style="color:#40e0d0;">Distribution:</b>
            Lower 25%: {low_count:,} cells &nbsp; | &nbsp;
            Middle 50%: {middle_count:,} cells &nbsp; | &nbsp;
            Upper 25%: {high_count:,} cells
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# IMMUNE STATE LABEL DISTRIBUTION
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check that immune-state labels were created
    if "Immune_State" in adata.obs.columns:

        # Count cells in each immune state
        state_counts = adata.obs["Immune_State"].value_counts()

        # --------------------------------------------------------
        # Section heading
        # --------------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 35px;">'
            'Immune State Classification'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8;">'
            'Distribution of cells across the dataset-derived immune states.'
            '</p>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Create three columns
        # --------------------------------------------------------
        col1, col2, col3 = st.columns(3)

        # Immune-Excluded
        with col1:
            st.metric(
                "Immune-Excluded",
                state_counts.get("Immune-Excluded", 0)
            )

        # Intermediate
        with col2:
            st.metric(
                "Intermediate",
                state_counts.get("Intermediate", 0)
            )

        # Inflamed
        with col3:
            st.metric(
                "Inflamed",
                state_counts.get("Inflamed", 0)
            )

# ============================================================
# ML DATASET SUMMARY
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check whether ML preparation was completed
    if "ml_info" in adata.uns:

        # Retrieve ML dataset information
        ml_info = adata.uns["ml_info"]

        # --------------------------------------------------------
        # Section heading
        # --------------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 35px;">'
            'Machine Learning Dataset'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8;">'
            'Features and samples prepared for immune-state classification.'
            '</p>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Display ML dataset statistics
        # --------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "ML Samples",
                f"{ml_info['samples']:,}"
            )

        with col2:
            st.metric(
                "Features",
                f"{ml_info['features']:,}"
            )

        with col3:
            st.metric(
                "Immune-Excluded",
                f"{ml_info['excluded_samples']:,}"
            )

        with col4:
            st.metric(
                "Inflamed",
                f"{ml_info['inflamed_samples']:,}"
            )


# ============================================================
# IMMUNE SCORE VISUALIZATIONS
# ============================================================

if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # --------------------------------------------------------
    # Check that all immune scores are available
    # --------------------------------------------------------
    required_scores = [
        "Tcell_score",
        "PDL1_myeloid_score",
        "Immune_State_Index"
    ]

    scores_available = all(
        score in adata.obs.columns
        for score in required_scores
    )

    if scores_available:

        # ----------------------------------------------------
        # Visualization section heading
        # ----------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 40px;">'
            'Immune Landscape'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8; margin-bottom: 20px;">'
            'Visual overview of immune-state signals across cells.'
            '</p>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # Create two equal dashboard columns
        # ----------------------------------------------------
        col1, col2 = st.columns(
            2,
            gap="large"
        )

        # ====================================================
        # LEFT: IMMUNE STATE INDEX DISTRIBUTION
        # ====================================================
        with col1:

            # Fixed-height heading area keeps both charts aligned
            st.markdown(
                """
                <div style="
                    height: 58px;
                    display: flex;
                    align-items: flex-start;
                ">
                    <h3 style="
                        margin: 0;
                        color: #f1f5f9;
                        font-size: 1.25rem;
                        line-height: 1.25;
                    ">
                        Immune State Index Distribution
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Create histogram
            fig_isi = px.histogram(
                adata.obs,
                x="Immune_State_Index",
                nbins=50,
                color_discrete_sequence=["#40e0d0"],
                labels={
                    "Immune_State_Index": "Immune State Index",
                    "count": "Cells"
                }
            )

            # Configure chart appearance
            fig_isi.update_layout(
                height=420,
                margin=dict(
                    l=55,
                    r=20,
                    t=15,
                    b=55
                ),
                paper_bgcolor="rgba(15, 23, 42, 0.75)",
                plot_bgcolor="rgba(15, 23, 42, 0.45)",
                font=dict(
                    color="#e2e8f0"
                ),
                xaxis=dict(
                    title="Immune State Index",
                    gridcolor="rgba(148, 163, 184, 0.15)"
                ),
                yaxis=dict(
                    title="Number of Cells",
                    gridcolor="rgba(148, 163, 184, 0.15)"
                )
            )

            # Display histogram
            st.plotly_chart(
                fig_isi,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

        # ====================================================
        # RIGHT: T-CELL VS PD-L1 / MYELOID
        # ====================================================
        with col2:

            # Fixed-height heading area keeps both charts aligned
            st.markdown(
                """
                <div style="
                    height: 58px;
                    display: flex;
                    align-items: flex-start;
                ">
                    <h3 style="
                        margin: 0;
                        color: #f1f5f9;
                        font-size: 1.25rem;
                        line-height: 1.25;
                    ">
                        T-cell vs PD-L1 / Myeloid
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Create scatter plot
            fig_scatter = px.scatter(
                adata.obs,
                x="Tcell_score",
                y="PDL1_myeloid_score",
                color_discrete_sequence=["#7dd3fc"],
                labels={
                    "Tcell_score": "T-cell Score",
                    "PDL1_myeloid_score":
                        "PD-L1 / Myeloid Score"
                },
                opacity=0.45
            )

            # Configure chart appearance
            fig_scatter.update_layout(
                height=420,
                margin=dict(
                    l=55,
                    r=20,
                    t=15,
                    b=55
                ),
                paper_bgcolor="rgba(15, 23, 42, 0.88)",
                plot_bgcolor="rgba(15, 23, 42, 0.65)",
                font=dict(
                    color="#e2e8f0"
                ),
                xaxis=dict(
                    title="T-cell Score",
                    gridcolor="rgba(148, 163, 184, 0.15)"
                ),
                yaxis=dict(
                    title="PD-L1 / Myeloid Score",
                    gridcolor="rgba(148, 163, 184, 0.15)"
                )
            )

            # Display scatter plot
            st.plotly_chart(
                fig_scatter,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

# ============================================================
# TRAIN / TEST SPLIT
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check whether the train/test split was created
    if "ml_split_info" in adata.uns:

        # Retrieve train/test information
        split_info = adata.uns["ml_split_info"]

        # --------------------------------------------------------
        # Section heading
        # --------------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 35px;">'
            'Train / Test Split'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8;">'
            'Stratified 80/20 split prepared for model training and evaluation.'
            '</p>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Display split statistics
        # --------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Training Samples",
                f"{split_info['train_samples']:,}"
            )

        with col2:
            st.metric(
                "Testing Samples",
                f"{split_info['test_samples']:,}"
            )

        with col3:
            st.metric(
                "Training Features",
                f"{split_info['train_features']:,}"
            )

        with col4:
            st.metric(
                "Testing Features",
                f"{split_info['test_features']:,}"
            )

        # --------------------------------------------------------
        # Display class distribution
        # --------------------------------------------------------

        st.html(
        f"""
        <div style="
            margin-top: 15px;
            padding: 12px 18px;
            border-radius: 10px;
            background: rgba(15, 23, 42, 0.70);
            color: #b8c7d9;
            font-size: 0.9rem;
        ">
            <div style="margin-bottom: 10px;">
                <b style="color:#40e0d0;">Training:</b>
                {split_info['train_excluded']:,} Immune-Excluded
                &nbsp; | &nbsp;
                {split_info['train_inflamed']:,} Inflamed
            </div>

            <div>
                <b style="color:#40e0d0;">Testing:</b>
                {split_info['test_excluded']:,} Immune-Excluded
                &nbsp; | &nbsp;
                {split_info['test_inflamed']:,} Inflamed
            </div>
        </div>
        """
        )

# ============================================================
# MODEL PERFORMANCE
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check whether model evaluation was completed
    if "model_evaluation" in adata.uns:

        # Retrieve evaluation results
        evaluation = adata.uns["model_evaluation"]

        # --------------------------------------------------------
        # Section heading
        # --------------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 35px;">'
            'Model Performance'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8;">'
            'Performance of the Logistic Regression classifier on unseen test data.'
            '</p>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Display evaluation metrics
        # --------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Accuracy",
                f"{evaluation['accuracy']:.3f}"
            )

        with col2:
            st.metric(
                "Precision",
                f"{evaluation['precision']:.3f}"
            )

        with col3:
            st.metric(
                "Recall",
                f"{evaluation['recall']:.3f}"
            )

        with col4:
            st.metric(
                "F1 Score",
                f"{evaluation['f1_score']:.3f}"
            )

# ============================================================
# CONFUSION MATRIX
# ============================================================
if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check whether model evaluation is available
    if "model_evaluation" in adata.uns:

        # Retrieve the confusion matrix
        evaluation = adata.uns["model_evaluation"]

        if "confusion_matrix" in evaluation:

            cm = evaluation["confusion_matrix"]

            # --------------------------------------------------------
            # Section heading
            # --------------------------------------------------------
            st.markdown(
                '<h2 style="color: #40e0d0; margin-top: 35px;">'
                'Confusion Matrix'
                '</h2>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<p style="color: #94a3b8;">'
                'Comparison of actual and predicted immune-state labels '
                'on the unseen test set.'
                '</p>',
                unsafe_allow_html=True
            )

            # --------------------------------------------------------
            # Create confusion matrix heatmap
            # --------------------------------------------------------
            fig_cm = px.imshow(
                cm,
                text_auto=True,
                x=["Immune-Excluded", "Inflamed"],
                y=["Immune-Excluded", "Inflamed"],
                labels={
                    "x": "Predicted Label",
                    "y": "Actual Label",
                    "color": "Number of Samples"
                },
                aspect="auto"
            )

            # --------------------------------------------------------
            # Configure chart appearance
            # --------------------------------------------------------
            fig_cm.update_layout(
                height=420,
                margin=dict(
                    l=55,
                    r=20,
                    t=40,
                    b=55
                ),
                paper_bgcolor="rgba(15, 23, 42, 0.88)",
                plot_bgcolor="rgba(15, 23, 42, 0.65)",
                font=dict(
                    color="#e2e8f0"
                )
            )

            # --------------------------------------------------------
            # Display confusion matrix
            # --------------------------------------------------------
            st.plotly_chart(
                fig_cm,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

if "adata" in st.session_state:

    # Retrieve the processed AnnData object
    adata = st.session_state["adata"]

    # Check whether feature importance was calculated
    if "feature_importance" in adata.uns:

        # Retrieve the feature importance table
        feature_importance = adata.uns["feature_importance"]

        # --------------------------------------------------------
        # Section heading
        # --------------------------------------------------------
        st.markdown(
            '<h2 style="color: #40e0d0; margin-top: 35px;">'
            'Important Genes'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<p style="color: #94a3b8;">'
            'Top genes contributing to the Logistic Regression classification.'
            '</p>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Feature importance chart
        # --------------------------------------------------------
        fig_importance = px.bar(
            feature_importance.sort_values(
                "Importance",
                ascending=True
            ),
            x="Importance",
            y="Gene",
            orientation="h",
            labels={
                "Importance": "Feature Importance",
                "Gene": "Gene"
            }
        )

        # --------------------------------------------------------
        # Configure chart appearance
        # --------------------------------------------------------
        fig_importance.update_layout(
            height=600,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=40
            ),
            paper_bgcolor="rgba(15, 23, 42, 0.88)",
            plot_bgcolor="rgba(15, 23, 42, 0.65)",
            font=dict(
                color="#e2e8f0"
            ),
            xaxis=dict(
                gridcolor="rgba(148, 163, 184, 0.15)"
            ),
            yaxis=dict(
                gridcolor="rgba(148, 163, 184, 0.15)"
            )
        )

        # --------------------------------------------------------
        # Display chart
        # --------------------------------------------------------
        st.plotly_chart(
            fig_importance,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        # --------------------------------------------------------
        # Display detailed gene table
        # --------------------------------------------------------
        st.markdown(
            '<h4 style="color: #e2e8f0; margin-top: 25px;">'
            'Top 20 Important Genes'
            '</h4>',
            unsafe_allow_html=True
        )

        st.dataframe(
            feature_importance,
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# AI BIOLOGICAL INTERPRETATION
# ============================================================

    if "ai_interpretation" in st.session_state:

        st.markdown(
            '<h2 style="color:#40e0d0; margin-top:35px;">'
            'AI Biological Interpretation'
            '</h2>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <p style="color:#94a3b8;">
                Concise interpretation generated from the completed
                computational analysis.
            </p>
            """,
            unsafe_allow_html=True
        )

        # --------------------------------------------------------
        # Display the LLM interpretation
        # --------------------------------------------------------

        with st.container(border=True):

            st.markdown(
                st.session_state["ai_interpretation"]
            )