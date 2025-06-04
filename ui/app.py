"""
Main Streamlit application for Job Search Assistant
"""

import sys
from pathlib import Path
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the src package
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src.agents.job_evaluation import evaluate_job_posting

# Load environment variables
load_dotenv()

# Set up the page
st.set_page_config(
    page_title="Job Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_job_evaluation_results(results: Dict[str, Any]) -> None:
    """Display job evaluation results in a formatted way"""
    recommendation = results.get("recommendation", "Unknown")
    reasoning = results.get("reasoning", "No reasoning provided")
    extracted_info = results.get("extracted_info", {})

    # Display recommendation with color coding
    if recommendation == "APPLY":
        st.success(f"🎯 **Recommendation: {recommendation}**")
        st.success(f"**Reasoning:** {reasoning}")
    else:
        st.error(f"❌ **Recommendation: {recommendation}**")
        st.error(f"**Reasoning:** {reasoning}")

    # Display extracted information
    if extracted_info:
        st.subheader("📋 Extracted Job Information")

        # Create columns for better layout
        col1, col2 = st.columns(2)

        with col1:
            if "job_title" in extracted_info:
                st.write(f"**Job Title:** {extracted_info['job_title']}")
            if "company_name" in extracted_info:
                st.write(f"**Company:** {extracted_info['company_name']}")
            if "location" in extracted_info:
                st.write(f"**Location:** {extracted_info['location']}")
            if "work_type" in extracted_info:
                st.write(f"**Work Type:** {extracted_info['work_type']}")

        with col2:
            if "salary_range" in extracted_info:
                salary = extracted_info["salary_range"]
                if isinstance(salary, dict):
                    min_sal = salary.get("min", "N/A")
                    max_sal = salary.get("max", "N/A")
                    st.write(f"**Salary Range:** ${min_sal} - ${max_sal}")
                else:
                    st.write(f"**Salary Range:** {salary}")

            if "experience_level" in extracted_info:
                exp_level = extracted_info["experience_level"]
                st.write(f"**Experience Level:** {exp_level}")
            if "employment_type" in extracted_info:
                emp_type = extracted_info["employment_type"]
                st.write(f"**Employment Type:** {emp_type}")

        # Display skills if available
        if "required_skills" in extracted_info:
            skills = extracted_info["required_skills"]
            if isinstance(skills, list):
                st.write(f"**Required Skills:** {', '.join(skills)}")
            else:
                st.write(f"**Required Skills:** {skills}")


def check_environment_setup() -> tuple[bool, str]:
    """Check if the environment is properly configured"""
    import os

    # Check for required API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        return False, "ANTHROPIC_API_KEY not found in environment variables"

    return True, "Environment is properly configured"


# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home"

# App header
st.title("🔍 Job Search Assistant")
st.markdown(
    """
A powerful AI-powered tool to streamline your job search process with
intelligent analysis.
"""
)

# Check environment setup
env_ok, env_message = check_environment_setup()
if not env_ok:
    st.error(f"⚠️ **Setup Required:** {env_message}")
    st.info(
        """
    **Setup Instructions:**
    1. Create a `.env` file in the root directory
    2. Add your Anthropic API key: `ANTHROPIC_API_KEY=your_key_here`
    3. Restart the Streamlit app

    Optional: Add Langfuse keys for observability:
    - `LANGFUSE_PUBLIC_KEY=your_public_key`
    - `LANGFUSE_SECRET_KEY=your_secret_key`
    - `LANGFUSE_ENABLED=true`
    """
    )

# Sidebar
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

# Main content based on selected page
if st.session_state.current_page == "🏠 Home":
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

elif st.session_state.current_page == "🎯 Job Evaluation":
    st.header("🎯 Job Evaluation")
    st.markdown(
        """
    Paste a job description below and our AI will analyze if it's a good fit
    based on your preferences.

    **Current evaluation criteria:**
    - 💰 Salary range ($160,000+ preferred)
    - 🏠 Remote work availability
    - 📊 Experience level match
    - 🛠️ Technical skills alignment
    """
    )

    # Job description input
    job_description = st.text_area(
        "Job Description",
        height=300,
        placeholder="Paste the complete job posting here...",
        help=(
            "Include the full job posting with requirements, "
            "responsibilities, and compensation details"
        ),
    )

    # Evaluation button and results
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        evaluate_btn = st.button(
            "🚀 Evaluate Job", type="primary", use_container_width=True
        )

    if evaluate_btn:
        if not job_description.strip():
            st.error("⚠️ Please enter a job description before evaluating.")
        elif not env_ok:
            st.error(
                "⚠️ Please configure your API keys first " "(see instructions above)."
            )
        else:
            # Show loading state
            with st.spinner("🔍 Analyzing job posting... This may take 10-30 seconds."):
                try:
                    # Call the job evaluation agent
                    results = evaluate_job_posting(
                        job_posting_text=job_description, enable_tracing=True
                    )

                    # Display results
                    st.divider()
                    st.subheader("📊 Evaluation Results")
                    display_job_evaluation_results(results)

                except Exception as e:
                    st.error(f"❌ **Error during evaluation:** {str(e)}")
                    st.info(
                        """
                    **Troubleshooting:**
                    - Check your API key configuration
                    - Ensure you have internet connectivity
                    - Try with a different job description
                    """
                    )

                    # Show error details in expander for debugging
                    with st.expander("🔧 Technical Details"):
                        st.code(str(e))

elif st.session_state.current_page == "📝 Resume Customization":
    st.header("📝 Resume Customization")
    st.info("🚧 **Coming Soon!** This feature is currently under development.")
    st.markdown(
        """
    **Planned Features:**
    - Upload your resume (PDF/Word)
    - Paste job description
    - Get a customized resume tailored to the specific role
    - Download the optimized version
    """
    )

elif st.session_state.current_page == "⚙️ Settings":
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

# Footer
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
