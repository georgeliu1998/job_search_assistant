"""
Main Streamlit application for Job Search Assistant
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Set APP_ENV for the application BEFORE importing config
if "APP_ENV" not in os.environ:
    os.environ["APP_ENV"] = "dev"

# Add the parent directory to the path so we can import the src package
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src.config import config
from src.utils.logging import get_app_logger, setup_logging

# Initialize logging for the Streamlit app
setup_logging(level=config.logging.level, format_string=config.logging.format)
logger = get_app_logger()

# Import UI modules
from ui.components.environment_check import render_environment_warning
from ui.pages.home import render_home_page
from ui.pages.job_evaluation import render_job_evaluation_page
from ui.pages.resume_customization import render_resume_customization_page
from ui.pages.settings import render_settings_page
from ui.utils.navigation import initialize_session_state, render_footer, render_sidebar

# Set up the page
st.set_page_config(
    page_title="Job Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
initialize_session_state()

# App header
st.title("🔍 Job Search Assistant")
st.markdown(f"{config.general.tagline}")

# Check environment setup and show warning if needed
render_environment_warning()

# Render sidebar navigation
page = render_sidebar()

# Main content based on selected page
if st.session_state.current_page == "🏠 Home":
    render_home_page()
elif st.session_state.current_page == "🎯 Job Evaluation":
    render_job_evaluation_page()
elif st.session_state.current_page == "📝 Resume Customization":
    render_resume_customization_page()
elif st.session_state.current_page == "⚙️ Settings":
    render_settings_page()

# Render footer
render_footer()
