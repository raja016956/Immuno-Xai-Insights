import streamlit as st


# ============================================================
# VANTA CELLS BACKGROUND
# ============================================================

VANTA_JS = """
export default function(component) {

    let vantaEffect = null;
    let background = null;

    function loadScript(src) {
        return new Promise((resolve, reject) => {

            // Already loaded
            if (
                src.includes("three") &&
                window.THREE
            ) {
                resolve();
                return;
            }

            if (
                src.includes("vanta") &&
                window.VANTA
            ) {
                resolve();
                return;
            }

            const script = document.createElement("script");

            script.src = src;
            script.onload = resolve;
            script.onerror = reject;

            document.head.appendChild(script);
        });
    }


    async function createBackground() {

        // Load Three.js
        await loadScript(
            "https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"
        );

        // Load Vanta CELLS
        await loadScript(
            "https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.cells.min.js"
        );


        // Remove an old background if one exists
        const oldBackground = document.getElementById(
            "immunoxai-vanta-background"
        );

        if (oldBackground) {
            oldBackground.remove();
        }


        // Create background element
        background = document.createElement("div");

        background.id = "immunoxai-vanta-background";

        background.style.position = "fixed";
        background.style.top = "0";
        background.style.left = "0";
        background.style.width = "100vw";
        background.style.height = "100vh";

        background.style.zIndex = "0";
        background.style.pointerEvents = "none";

        background.style.opacity = "0.65";


        document.body.appendChild(background);


        // Create Vanta effect
        vantaEffect = VANTA.CELLS({

            el: background,

            mouseControls: false,
            touchControls: false,
            gyroControls: false,

            minHeight: 200.00,
            minWidth: 200.00,

            scale: 1.00,
            scaleMobile: 1.00,

            color1: 0x4eeded,
            color2: 0x837e37,

            size: 2.5,
            speed: 1.5
        });


        // Keep Streamlit content above background
        const app = document.querySelector(
            '[data-testid="stAppViewContainer"]'
        );

        if (app) {
            app.style.position = "relative";
            app.style.zIndex = "1";
        }


        const main = document.querySelector(
            '[data-testid="stMain"]'
        );

        if (main) {
            main.style.background = "transparent";
        }
    }


    createBackground();


    // Cleanup when component is removed
    return () => {

        if (vantaEffect) {
            vantaEffect.destroy();
            vantaEffect = null;
        }

        if (background) {
            background.remove();
            background = null;
        }
    };
}
"""


# Register the Vanta component
vanta_background = st.components.v2.component(
    name="immunoxai_vanta_background",
    js=VANTA_JS,
    isolate_styles=False
)


def apply_style():

    # Start Vanta background
    vanta_background()


    # ============================================================
    # STREAMLIT CSS
    # ============================================================

    st.markdown(
        """
        <style>

        /* Main application */
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }


        /* Main content */
        [data-testid="stMain"] {
            background: transparent !important;
            position: relative;
            z-index: 1;
        }


        /* Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(10, 14, 23, 0.85) !important;

            backdrop-filter: blur(12px);

            border-right: 1px solid rgba(64, 224, 208, 0.20);

            position: relative;
            z-index: 2;
        }


        /* Top header */
        [data-testid="stHeader"] {
            background: transparent !important;
        }


        /* ImmunoXAI title */
        .glow-text {
            color: #40e0d0;

            text-shadow:
                0 0 5px rgba(64, 224, 208, 0.4),
                0 0 15px rgba(64, 224, 208, 0.25);

            font-weight: 600;
        }


        /* Glass containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            position: relative !important;
            z-index: 5 !important;

            background: rgba(10, 14, 23, 0.55) !important;
            background-color: rgba(10, 14, 23, 0.55) !important;

            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);

            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 14px;
        }
                </style>
        """,
        unsafe_allow_html=True
    )