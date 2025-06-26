"""
Home page for the Job Search Assistant
"""

import streamlit as st


def render_home_page():
    """Render the home page content"""
    st.header("Welcome to Job Search Assistant")
    st.markdown(
        """
    ### 🚀 How to use this tool:
    1. **🎯 Job Evaluation** - Analyze job descriptions to determine if
       they're a good fit
    2. **📝 Resume Customization** - Tailor your resume for specific
       opportunities *(Coming Soon)*
    3. **⚙️ Settings** - Configure your preferences and upload your
       resume *(Coming Soon)*
    """
    )

    # Feature cards
    st.subheader("✨ Features")
    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
        ### 🎯 Job Evaluation
        **Currently Available**

        Analyze job descriptions using AI to determine if they match
        your criteria:
        - Salary requirements
        - Remote work preferences
        - Experience level fit
        - Skills alignment
        """
        )
        if st.button("Try Job Evaluation", key="job_eval_btn", type="primary"):
            st.session_state.current_page = "🎯 Job Evaluation"
            st.rerun()

    with col2:
        st.warning(
            """
        ### 📝 Resume Customization
        **Coming Soon**

        Automatically tailor your resume to highlight relevant skills:
        - Match job requirements
        - Optimize keywords
        - Customize experience descriptions
        - Generate cover letters
        """
        )
