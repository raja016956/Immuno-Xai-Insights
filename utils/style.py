import streamlit as st
import base64
from pathlib import Path

# ============================================================
# IMMUNOXAI MICROSCOPIC CELL BACKGROUND
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

BACKGROUND_PATH = (
    BASE_DIR
    / "assets"
    / "immunoxai_cells_background.png"
)

CELLS_DIR = (
    BASE_DIR
    / "assets"
    / "cells"
)


# ------------------------------------------------------------
# Load stationary background
# ------------------------------------------------------------

with open(BACKGROUND_PATH, "rb") as image_file:

    BACKGROUND_BASE64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")


# ------------------------------------------------------------
# Load individual cell sprites
# ------------------------------------------------------------

CELL_SPRITES = []

for cell_file in sorted(CELLS_DIR.glob("cell_*.png")):

    with open(cell_file, "rb") as image_file:

        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

        CELL_SPRITES.append(encoded)


# ------------------------------------------------------------
# Cell positions and animation settings
# ------------------------------------------------------------

CELL_SETTINGS = [

    # left / upper
    {
        "left": "-2%",
        "top": "18%",
        "size": "115px",
        "duration": "40s",
        "delay": "-12s",
    },

    {
        "left": "12%",
        "top": "4%",
        "size": "170px",
        "duration": "50s",
        "delay": "-30s",
    },

    {
        "left": "30%",
        "top": "20%",
        "size": "90px",
        "duration": "35s",
        "delay": "-8s",
    },

    {
        "left": "61%",
        "top": "10%",
        "size": "105px",
        "duration": "57s",
        "delay": "-25s",
    },

    # right
    {
        "left": "88%",
        "top": "8%",
        "size": "210px",
        "duration": "62s",
        "delay": "-40s",
    },

    # lower area
    {
        "left": "10%",
        "top": "63%",
        "size": "75px",
        "duration": "35s",
        "delay": "-15s",
    },

    {
        "left": "30%",
        "top": "82%",
        "size": "125px",
        "duration": "50s",
        "delay": "-32s",
    },

    {
        "left": "54%",
        "top": "78%",
        "size": "140px",
        "duration": "60s",
        "delay": "-20s",
    },

    {
        "left": "70%",
        "top": "84%",
        "size": "90px",
        "duration": "43s",
        "delay": "-7s",
    },

    {
        "left": "87%",
        "top": "70%",
        "size": "220px",
        "duration": "55s",
        "delay": "-45s",
    },

]

def apply_style():

    # --------------------------------------------------------
    # Create individual animated cell elements
    # --------------------------------------------------------

    cells_html = ""

    for i, (sprite, settings) in enumerate(
        zip(CELL_SPRITES, CELL_SETTINGS)
    ):

        cells_html += f"""
        <div
            class="immunoxai-cell cell-{i}"
            style="
                left:{settings['left']};
                top:{settings['top']};
                width:{settings['size']};
                height:{settings['size']};

                background-image:
                    url('data:image/png;base64,{sprite}');

                animation-duration:
                    {settings['duration']};

                animation-delay:
                    {settings['delay']};
            "
        ></div>
        """


    # --------------------------------------------------------
    # Main CSS
    # --------------------------------------------------------

    st.markdown(
        f"""
        <style>

        /* =====================================================
           STATIONARY MICROSCOPIC BACKGROUND
           ===================================================== */

        #immunoxai-cell-background {{

            position: fixed;

            top: 0;
            left: 0;

            width: 100vw;
            height: 100vh;

            z-index: 0;

            pointer-events: none;

            background-image:
                url(
                    "data:image/png;base64,{BACKGROUND_BASE64}"
                );

            background-size: cover;

            background-position: center;

            background-repeat: no-repeat;

            opacity: 0.58;

        }}


        /* =====================================================
           DARK ATMOSPHERIC OVERLAY
           ===================================================== */

        #immunoxai-cell-overlay {{

            position: fixed;

            top: 0;
            left: 0;

            width: 100vw;
            height: 100vh;

            z-index: 0;

            pointer-events: none;

            background:
                rgba(2, 8, 12, 0.30);

        }}


        /* =====================================================
           INDIVIDUAL CELLS
           ===================================================== */

        .immunoxai-cell {{

            position: fixed;

            z-index: 0;

            pointer-events: none;

            user-select: none;

            background-size: contain;

            background-position: center;

            background-repeat: no-repeat;

            opacity: 0.72;

            animation-name:
                immunoxai-cell-drift;

            animation-timing-function:
                ease-in-out;

            animation-iteration-count:
                infinite;

            animation-direction:
                alternate;

            will-change:
                transform;

        }}


        /* =====================================================
           INDEPENDENT CELL MOVEMENT
           ===================================================== */

        @keyframes immunoxai-cell-drift {{

            0% {{
                transform:
                    translate3d(0px, 0px, 0px)
                    scale(1);
            }}

            25% {{
                transform:
                    translate3d(35px, -25px, 0px)
                    scale(1.03);
            }}

            50% {{
                transform:
                    translate3d(-30px, 35px, 0px)
                    scale(1.06);
            }}

            75% {{
                transform:
                    translate3d(40px, 20px, 0px)
                    scale(1.03);
            }}

            100% {{
                transform:
                    translate3d(-25px, -35px, 0px)
                    scale(1);
            }}

        }}

        /* =====================================================
           STREAMLIT MAIN AREA
           ===================================================== */

        [data-testid="stAppViewContainer"] {{

            background:
                transparent !important;

        }}


        [data-testid="stMain"] {{

            background:
                rgba(2, 8, 12, 0.22) !important;

            position: relative;

            z-index: 1;

        }}


        [data-testid="stHeader"] {{

            background:
                transparent !important;

        }}


        /* =====================================================
           SIDEBAR
           ===================================================== */

        [data-testid="stSidebar"] {{

            background:
                rgba(5, 10, 16, 0.94) !important;

            backdrop-filter:
                blur(12px);

            border-right:
                1px solid
                rgba(64, 224, 208, 0.20);

            position:
                relative;

            z-index:
                5;

        }}


        /* =====================================================
           TITLE GLOW
           ===================================================== */

        .glow-text {{

            color:
                #40e0d0;

            text-shadow:
                0 0 5px
                rgba(64, 224, 208, 0.4),

                0 0 15px
                rgba(64, 224, 208, 0.25);

            font-weight:
                600;

        }}


        /* =====================================================
           DARK SUMMARY CARDS
           ===================================================== */

        .st-key-summary_card_1,
        .st-key-summary_card_2,
        .st-key-summary_card_3,
        [class*="st-key-report_history_card_"],
        [class*="st-key-biological_interpretation_"],
        [class*="st-key-report_card_"],
        [class*="st-key-ai_interpretation_"],
        .st-key-upload_box,
        .st-key-llm_interpretation,
        .st-key-no_reports{{

            background:
                rgba(5, 10, 16, 0.94) !important;

            background-color:
                rgba(5, 10, 16, 0.94) !important;

            border:
                1px solid
                rgba(64, 224, 208, 0.22) !important;

            border-radius:
                14px !important;

            backdrop-filter:
                blur(10px);

            -webkit-backdrop-filter:
                blur(10px);

        }}

        /* =====================================================
           ANIMATED CELL CONTAINER
           ===================================================== */

        #immunoxai-animated-cells {{
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }}


        .immunoxai-cell {{
            position: fixed;
            z-index: 0;
            pointer-events: none;
            user-select: none;

            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;

            opacity: 0.72;

            animation-name:
                immunoxai-cell-drift;

            animation-timing-function:
                ease-in-out;

            animation-iteration-count:
                infinite;

            animation-direction:
                alternate;

            will-change:
                transform;
        }}

        </style>

        </style>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # Background HTML
    # --------------------------------------------------------

    st.html(
        f"""
        <div id="immunoxai-cell-background"></div>
        <div id="immunoxai-cell-overlay"></div>

        <div id="immunoxai-animated-cells">
            {cells_html}
        </div>
        """
    )
