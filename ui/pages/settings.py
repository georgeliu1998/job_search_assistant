"""
Settings page for user preferences and configuration
"""

import streamlit as st


def render_settings_page():
    """Render the settings page content"""
    st.header("⚙️ Settings")
    st.info(
        "🚧 **Coming Soon!** User preferences and resume management "
        "will be available here."
    )

    st.subheader("📋 Current Evaluation Criteria")
    st.markdown(
        """
    The job evaluation currently uses these built-in criteria:

    - **💰 Minimum Salary:** $160,000/year
    - **🏠 Work Location:** Remote preferred
    - **📊 Experience Level:** 3-8 years preferred
    - **🛠️ Technical Skills:** Python, ML, Data Science focus

    *Customizable preferences will be available in a future update.*
    """
    )
