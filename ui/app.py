"""
Main Streamlit application for Job Search Assistant
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# Add the parent directory to the path so we can import the src package
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Set APP_ENV for the application
if "APP_ENV" not in os.environ:
    os.environ["APP_ENV"] = "dev"

from src.agents.job_evaluation import evaluate_job_posting
from src.config import config
from src.utils.logging import get_app_logger, setup_logging

# Initialize logging for the Streamlit app
setup_logging(level=config.logging.level, format_string=config.logging.format)
logger = get_app_logger()

# Set up the page
st.set_page_config(
    page_title="Job Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_job_evaluation_results(results: Dict[str, Any]) -> None:
    """Display job evaluation results in a formatted way"""
    # Handle errors
    if "error" in results:
        st.error(f"❌ **Error:** {results['error']}")
        return

    evaluation_result = results.get("evaluation_result", {})
    extracted_info = results.get("extracted_info", {})

    # Handle evaluation errors
    if "error" in evaluation_result:
        st.error(f"❌ **Evaluation Error:** {evaluation_result['error']}")
        return

    # Calculate overall recommendation
    if not evaluation_result:
        st.error("❌ **Recommendation: Unknown**")
        st.error("**Reasoning:** No evaluation results available")
        return

    # Count passed criteria
    passed_criteria = []
    failed_criteria = []

    for criterion, result in evaluation_result.items():
        if isinstance(result, dict) and "pass" in result:
            if result["pass"]:
                passed_criteria.append(criterion)
            else:
                failed_criteria.append(criterion)

    total_criteria = len(passed_criteria) + len(failed_criteria)
    passed_count = len(passed_criteria)

    # Generate recommendation based on results
    if passed_count == total_criteria:
        recommendation = "APPLY"
        reasoning = f"All {total_criteria} criteria met!"
    elif passed_count >= total_criteria * 0.6:  # 60% threshold for consideration
        recommendation = "CONSIDER"
        reasoning = f"{passed_count}/{total_criteria} criteria met"
    else:
        recommendation = "SKIP"
        reasoning = f"Only {passed_count}/{total_criteria} criteria met"

    # Display recommendation with color coding
    if recommendation == "APPLY":
        st.success(f"🎯 **Recommendation: {recommendation}**")
        st.success(f"**Reasoning:** {reasoning}")
    elif recommendation == "CONSIDER":
        st.warning(f"🤔 **Recommendation: {recommendation}**")
        st.warning(f"**Reasoning:** {reasoning}")
    else:
        st.error(f"❌ **Recommendation: {recommendation}**")
        st.error(f"**Reasoning:** {reasoning}")

    # Display detailed evaluation results
    st.subheader("📊 Evaluation Results")

    for criterion, result in evaluation_result.items():
        if isinstance(result, dict) and "pass" in result:
            criterion_name = criterion.replace("_", " ").title()
            if result["pass"]:
                st.success(f"✅ **{criterion_name}**: {result['reason']}")
            else:
                st.error(f"❌ **{criterion_name}**: {result['reason']}")

    # Display extracted information
    if extracted_info:
        st.subheader("📋 Extracted Job Information")

        # Create columns for better layout
        col1, col2 = st.columns(2)

        with col1:
            if "title" in extracted_info:
                st.write(f"**Job Title:** {extracted_info['title']}")
            if "company" in extracted_info:
                st.write(f"**Company:** {extracted_info['company']}")
            if "location_policy" in extracted_info:
                st.write(f"**Location Policy:** {extracted_info['location_policy']}")
            if "role_type" in extracted_info:
                st.write(f"**Role Type:** {extracted_info['role_type']}")

        with col2:
            if "salary_min" in extracted_info or "salary_max" in extracted_info:
                min_sal = extracted_info.get("salary_min", "N/A")
                max_sal = extracted_info.get("salary_max", "N/A")
                if min_sal and max_sal:
                    st.write(f"**Salary Range:** ${min_sal:,} - ${max_sal:,}")
                elif max_sal:
                    st.write(f"**Salary Range:** Up to ${max_sal:,}")
                elif min_sal:
                    st.write(f"**Salary Range:** From ${min_sal:,}")
                else:
                    st.write("**Salary Range:** Not specified")


def check_environment_setup() -> tuple[bool, str]:
    """Check if the environment is properly configured"""
    logger.debug("Checking environment setup...")
    try:
        # Check if configs can be loaded
        # configs is already imported at module level
        logger.debug(f"Current APP_ENV: {os.getenv('APP_ENV')}")

        # Check if at least one LLM profile has an API key
        has_valid_profile = False
        for profile_name, profile in config.llm_profiles.items():
            logger.debug(
                f"Checking profile {profile_name}: has_api_key={bool(profile.api_key)}"
            )
            if profile.api_key:
                has_valid_profile = True
                break

        if not has_valid_profile:
            logger.warning("No LLM profiles have valid API keys configured")
            return False, "No LLM profiles have valid API keys configured"

        logger.info("Environment setup check passed")
        return True, "Environment is properly configured"
    except Exception as e:
        logger.error(f"Environment setup check failed: {e}", exc_info=True)
        return False, f"Configuration error: {str(e)}"


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
            logger.warning("User attempted to evaluate empty job description")
            st.error("⚠️ Please enter a job description before evaluating.")
        elif not env_ok:
            logger.warning("User attempted evaluation with invalid environment setup")
            st.error(
                "⚠️ Please configure your API keys first " "(see instructions above)."
            )
        else:
            # Show loading state
            logger.info("Starting job evaluation process")
            logger.debug(f"Job description length: {len(job_description)} characters")
            with st.spinner("🔍 Analyzing job posting... This may take 10-30 seconds."):
                try:
                    # Call the job evaluation agent
                    logger.debug("Calling evaluate_job_posting function")
                    results = evaluate_job_posting(job_description)
                    logger.info("Job evaluation completed successfully")
                    logger.debug(f"Results: {results}")

                    # Display results
                    st.divider()
                    st.subheader("📊 Evaluation Results")
                    display_job_evaluation_results(results)

                except Exception as e:
                    logger.error(f"Job evaluation failed: {e}", exc_info=True)
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
