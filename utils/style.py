import streamlit as st


# ============================================================
# VANTA CELLS BACKGROUND
# ============================================================

PARTICLES_JS = """
export default function(component) {

    const container = document.createElement("div");

    container.id = "immunoxai-particles";

    container.style.position = "fixed";
    container.style.top = "0";
    container.style.left = "0";
    container.style.width = "100vw";
    container.style.height = "100vh";

    container.style.zIndex = "0";
    container.style.pointerEvents = "none";

    document.body.appendChild(container);


    function loadScript(src) {

        return new Promise((resolve, reject) => {

            if (window.tsParticles) {
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


    async function createParticles() {

        await loadScript(
            "https://cdn.jsdelivr.net/npm/@tsparticles/engine@4/tsparticles.engine.min.js"
        );

        await loadScript(
            "https://cdn.jsdelivr.net/npm/@tsparticles/slim@4/tsparticles.slim.bundle.min.js"
        );

        await window.loadSlim(window.tsParticles);


        await window.tsParticles.load({

            id: "immunoxai-particles",

            options: {

                fullScreen: {
                    enable: false
                },

                background: {
                    color: "#071116"
                },

                fpsLimit: 40,

                particles: {

                    number: {
                        value: 55
                    },

                    color: {
                        value: [
                            "#40e0d0",
                            "#b8ffff",
                            "#ffffff"
                        ]
                    },

                    opacity: {
                        value: 0.35
                    },

                    size: {
                        value: {
                            min: 1,
                            max: 2.5
                        }
                    },

                    move: {

                        enable: true,

                        speed: 0.35,

                        direction: "none",

                        outModes: {
                            default: "bounce"
                        }
                    },

                    links: {

                        enable: true,

                        distance: 140,

                        color: "#40e0d0",

                        opacity: 0.18,

                        width: 1
                    }
                },

                detectRetina: true
            }

        });

    }


    createParticles();


    return () => {

        const existing = document.getElementById(
            "immunoxai-particles"
        );

        if (existing) {
            existing.remove();
        }

    };
}
"""


particles_background = st.components.v2.component(
    name="immunoxai_particles_background",
    js=PARTICLES_JS,
    isolate_styles=False
)


def apply_style():

    # Start Vanta background
    particles_background()


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