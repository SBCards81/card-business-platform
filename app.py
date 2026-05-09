import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(
    page_title="The Juice Card Platform",
    page_icon="🧃",
    layout="wide"
)

# --------------------------------------------------
# BRAND STYLING
# Uses your GitHub file: juice-bg.PNG
# --------------------------------------------------
st.markdown("""
<style>

/* APP BACKGROUND — centered logo, visible but not blown up */
.stApp {
    background-color: #f6efe4;
    background-image:
        linear-gradient(
            rgba(255, 255, 255, 0.34),
            rgba(255, 255, 255, 0.34)
        ),
