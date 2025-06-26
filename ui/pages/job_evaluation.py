"""
Job Evaluation page for analyzing job postings
"""

import streamlit as st

from src.agents.job_evaluation import evaluate_job_posting
from ui.components.environment_check import check_environment_setup
from ui.components.job_results import display_job_evaluation_results


def render_job_evaluation_page():
    """Render the job evaluation page content"""
    st.header("🎯 Job Evaluation")
    st.markdown(
        """
    Paste a job description below and our AI will analyze if it's a good fit
    based on your preferences.

    **Current evaluation criteria:**
    - 💰 Salary range ($100,000+ preferred)
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
        else:
            env_ok, _ = check_environment_setup()
            if not env_ok:
                st.error(
                    "⚠️ Please configure your API keys first "
                    "(see instructions above)."
                )
            else:
                # Show loading state
                with st.spinner(
                    "🔍 Analyzing job posting... This may take several seconds."
                ):
                    try:
                        # Call the job evaluation agent
                        results = evaluate_job_posting(job_description)

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
