import streamlit as st

# st.image("https://www.svgrepo.com/show/449355/dna.svg").title("ImmunoXAI")

# col1, col2 = st.columns(2)

# sb1 = st.sidebar.text("Immuno Xai Platform")
# sb1 = st.sidebar.header("Dashboard")
# sb2 = st.sidebar.header("upload dataset")
# sb2 = st.sidebar.header("Analysis")
# sb1 = st.sidebar.header("Reports")


dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True)
analysis_page = st.Page("pages/Analysis.py", title="Analysis", icon=":material/analytics:")
reports_page = st.Page("pages/Reports.py", title="Reports", icon=":material/analytics:")

pg = st.navigation([dashboard_page, analysis_page,reports_page ])
pg.run()