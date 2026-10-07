import streamlit as st
from utils.style import apply_style


dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True)
analysis_page = st.Page("pages/Analysis.py", title="Analysis", icon=":material/analytics:")
reports_page = st.Page("pages/Reports.py", title="Reports", icon=":material/analytics:")

pg = st.navigation([dashboard_page, analysis_page,reports_page ])
pg.run()