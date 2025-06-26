"""
Navigation utilities for the Streamlit app
"""

import streamlit as st


def initialize_session_state():
    """Initialize session state for page navigation"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "🏠 Home"


def render_sidebar():
    """Render the sidebar navigation"""
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a feature",
        ["🏠 Home", "🎯 Job Evaluation", "📝 Resume Customization", "⚙️ Settings"],
        index=[
            "🏠 Home",
            "🎯 Job Evaluation",
            "📝 Resume Customization",
            "⚙️ Settings",
        ].index(st.session_state.current_page),
    )

    # Update session state when radio button changes
    if page != st.session_state.current_page:
        st.session_state.current_page = page

    return page


def render_footer():
    """Render the app footer"""
    st.divider()
    st.markdown(
        """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        © 2025 Job Search Assistant |
        <a href='https://github.com/georgeliu1998/job_search_assistant'
           target='_blank'>GitHub</a>
    </div>
    """,
        unsafe_allow_html=True,
    )
