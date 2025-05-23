"""
Main Streamlit application for Job Search Assistant
"""

import sys
from pathlib import Path

import streamlit as st

# Add the parent directory to the path so we can import the src package
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src.config import settings

# Set up the page
st.set_page_config(
    page_title="Job Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# App header
st.title("Job Search Assistant")
st.markdown(
    """
A powerful tool to streamline your job search process with AI-powered analysis.
"""
)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page", ["Home", "Job Evaluation", "Resume Customization", "Settings"]
)

# Main content based on selected page
if page == "Home":
    st.header("Welcome to Job Search Assistant")
    st.markdown(
        """
    ### How to use this tool:
    1. Go to **Settings** to upload your resume and set your job preferences
    2. Use **Job Evaluation** to analyze job descriptions and determine if they're a good fit
    3. For promising opportunities, use **Resume Customization** to tailor your resume
    """
    )

    # Example cards
    st.subheader("Getting Started")
    col1, col2 = st.columns(2)

    with col1:
        st.info("### Job Evaluation")
        st.markdown(
            "Analyze job descriptions to find the best matches for your skills and preferences."
        )
        st.button("Try Job Evaluation", key="job_eval_btn")

    with col2:
        st.info("### Resume Customization")
        st.markdown(
            "Automatically tailor your resume to highlight relevant skills for specific job opportunities."
        )
        st.button("Try Resume Customization", key="resume_btn")

elif page == "Job Evaluation":
    st.header("Job Evaluation")
    st.markdown("Paste a job description below to analyze if it's a good fit for you.")

    job_description = st.text_area("Job Description", height=300)

    if st.button("Evaluate Job"):
        if job_description:
            # This would connect to the backend in the real implementation
            st.info(
                "Job evaluation functionality will be implemented in a future update."
            )
            # Placeholder for evaluation result
            st.success("✅ This job is a good match for your profile!")
        else:
            st.error("Please enter a job description.")

elif page == "Resume Customization":
    st.header("Resume Customization")
    st.markdown("Upload a job description to customize your resume.")

    job_description = st.text_area("Job Description", height=300)

    if st.button("Customize Resume"):
        if job_description:
            # This would connect to the backend in the real implementation
            st.info(
                "Resume customization functionality will be implemented in a future update."
            )
            # Placeholder for customized resume
            st.success("Resume customized successfully!")
        else:
            st.error("Please enter a job description.")

elif page == "Settings":
    st.header("Settings")

    st.subheader("Resume")
    resume_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

    st.subheader("Job Preferences")
    with st.form("job_preferences_form"):
        desired_roles = st.text_input("Desired Job Titles (comma separated)")
        required_skills = st.text_area("Required Skills (comma separated)")
        preferred_locations = st.text_input("Preferred Locations (comma separated)")
        remote_preference = st.selectbox(
            "Remote Work Preference",
            ["No Preference", "Remote Only", "Hybrid", "On-site"],
        )

        min_exp, max_exp = st.slider(
            "Years of Experience", min_value=0, max_value=20, value=(0, 5)
        )

        min_salary, max_salary = st.slider(
            "Salary Range ($)",
            min_value=0,
            max_value=500000,
            value=(50000, 150000),
            step=10000,
        )

        other_preferences = st.text_area("Other Preferences")

        submitted = st.form_submit_button("Save Preferences")
        if submitted:
            st.success("Preferences saved successfully!")

# Footer
st.markdown("---")
st.markdown(
    "© 2025 Job Search Assistant | [GitHub](https://github.com/georgeliu1998/job_search_assistant)"
)
