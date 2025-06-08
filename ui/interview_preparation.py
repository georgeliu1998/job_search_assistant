"""
Interview Preparation page for the Job Search Assistant.
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Add the parent directory to the path so we can import the src package
parent_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

from src.agents.interview_preparation import InterviewPreparationAgent
from src.models.interview import InterviewPrepInput, InterviewType
from src.utils.pdf_processor import (
    extract_text_from_pdf,
    get_pdf_info,
    validate_pdf_file,
)


def _get_streamlit_secret(key: str) -> str:
    """Safely get a Streamlit secret without throwing an error if secrets don't exist."""
    try:
        return st.secrets.get(key)
    except:
        return None


def show_interview_preparation_page():
    """Display the interview preparation page."""
    st.header("🎤 Interview Preparation")
    st.markdown(
        """
    Get personalized interview prep based on your specific situation.
    Provide your job description, resume, and interview details to receive
    a comprehensive preparation guide.
    """
    )

    # Check for Gemini API key (environment variables, Streamlit secrets, or session state)
    gemini_api_key = (
        os.getenv("GEMINI_API_KEY")
        or st.session_state.get("gemini_api_key")
        or _get_streamlit_secret("GEMINI_API_KEY")
    )

    if not gemini_api_key:
        st.error("⚠️ **Gemini API Key Required**")
        st.info(
            """
        **Setup Instructions:**
        1. **Option A (Recommended)**: Add to `.env` file: `GEMINI_API_KEY=your_key_here`
        2. **Option B**: Add to Streamlit secrets: Create `.streamlit/secrets.toml` with `GEMINI_API_KEY="your_key_here"`
        3. Restart the app after adding the key

        Get your API key from: https://makersuite.google.com/app/apikey
        """
        )
        return

    # Form for interview preparation
    with st.form("interview_prep_form"):
        st.subheader("📋 Required Information")

        # Job Description (Required)
        job_description = st.text_area(
            "Job Description *",
            height=200,
            placeholder="Paste the full job description here...",
            help="Include the complete job posting for best results",
        )

        # Interview Type (Required)
        interview_type = st.selectbox(
            "Interview Type *",
            options=[e.value for e in InterviewType],
            help="Select the type of interview you're preparing for",
        )

        # Resume Section
        st.subheader("📄 Resume *")
        resume_option = st.radio(
            "How would you like to provide your resume?",
            ["Upload PDF", "Paste text"],
            help="Choose the most convenient way to provide your resume",
        )

        resume_text = ""
        if resume_option == "Upload PDF":
            resume_file = st.file_uploader(
                "Upload Resume PDF", type="pdf", help="Upload your resume as a PDF file"
            )

            if resume_file:
                try:
                    # Validate PDF
                    if validate_pdf_file(resume_file):
                        # Show PDF info
                        pdf_info = get_pdf_info(resume_file)
                        if pdf_info:
                            st.success(f"✅ PDF loaded: {pdf_info['num_pages']} pages")

                        # Extract text
                        resume_text = extract_text_from_pdf(resume_file)
                        if resume_text:
                            st.success(
                                f"✅ Resume text extracted ({len(resume_text)} characters)"
                            )
                            # Show preview
                            with st.expander("Preview extracted text"):
                                st.text(
                                    resume_text[:500] + "..."
                                    if len(resume_text) > 500
                                    else resume_text
                                )
                        else:
                            st.warning("⚠️ No text could be extracted from the PDF")
                    else:
                        st.error("❌ Invalid PDF file or unable to read")
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {str(e)}")
        else:
            resume_text = st.text_area(
                "Paste resume text *",
                height=200,
                placeholder="Paste your resume content here...",
                help="Include your complete resume text",
            )

        # Optional Details Section
        st.subheader("🔍 Optional Details")

        col1, col2 = st.columns(2)
        with col1:
            interviewer_name = st.text_input(
                "Interviewer Name",
                placeholder="e.g., John Smith",
                help="Name of the person who will interview you",
            )

            interviewer_title = st.text_input(
                "Interviewer Title",
                placeholder="e.g., Technical Talent Partner",
                help="Job title or role of the interviewer",
            )

        with col2:
            company_website = st.text_input(
                "Company Website URL",
                placeholder="https://www.company.com",
                help="Company website for additional context",
            )

        # LinkedIn Profile Section
        st.subheader("💼 Interviewer LinkedIn Profile (Optional)")
        linkedin_option = st.radio(
            "Provide interviewer's LinkedIn information?",
            ["None", "Upload PDF", "Paste profile text/URL"],
            help="Additional context about the interviewer can help personalize your preparation",
        )

        interviewer_linkedin = None
        if linkedin_option == "Upload PDF":
            linkedin_file = st.file_uploader(
                "Upload LinkedIn Profile PDF",
                type="pdf",
                help="Upload a PDF export of the interviewer's LinkedIn profile",
            )

            if linkedin_file:
                try:
                    if validate_pdf_file(linkedin_file):
                        interviewer_linkedin = extract_text_from_pdf(linkedin_file)
                        if interviewer_linkedin:
                            st.success(
                                f"✅ LinkedIn profile extracted ({len(interviewer_linkedin)} characters)"
                            )
                            with st.expander("Preview LinkedIn text"):
                                st.text(
                                    interviewer_linkedin[:300] + "..."
                                    if len(interviewer_linkedin) > 300
                                    else interviewer_linkedin
                                )
                    else:
                        st.error("❌ Invalid PDF file")
                except Exception as e:
                    st.error(f"❌ Error processing LinkedIn PDF: {str(e)}")

        elif linkedin_option == "Paste profile text/URL":
            interviewer_linkedin = st.text_area(
                "LinkedIn Profile URL or Text",
                height=100,
                placeholder="Paste LinkedIn URL or profile information...",
                help="You can paste the LinkedIn URL or copy/paste profile text",
            )

        # Generate button
        submitted = st.form_submit_button(
            "🚀 Generate Interview Guide",
            type="primary",
            help="Generate your personalized interview preparation guide",
        )

    # Process form submission
    if submitted:
        # Validation
        if not job_description.strip():
            st.error("❌ Please provide a job description")
            return

        if not resume_text.strip():
            st.error("❌ Please provide your resume (either upload PDF or paste text)")
            return

        # Show processing message
        with st.spinner(
            "🤖 Generating your personalized interview guide... This may take a moment."
        ):
            try:
                # Use the API key we already found
                api_key = gemini_api_key

                # Create agent
                agent = InterviewPreparationAgent(gemini_api_key=api_key)

                # Prepare input (convert interview_type string back to enum)
                interview_type_enum = None
                for enum_item in InterviewType:
                    if enum_item.value == interview_type:
                        interview_type_enum = enum_item
                        break

                if not interview_type_enum:
                    st.error(f"❌ Invalid interview type: {interview_type}")
                    return

                input_data = InterviewPrepInput(
                    job_description=job_description,
                    interview_type=interview_type_enum,
                    resume_text=resume_text,
                    interviewer_name=(
                        interviewer_name.strip() if interviewer_name else None
                    ),
                    interviewer_title=(
                        interviewer_title.strip() if interviewer_title else None
                    ),
                    interviewer_linkedin=(
                        interviewer_linkedin.strip() if interviewer_linkedin else None
                    ),
                    company_website=(
                        company_website.strip() if company_website else None
                    ),
                )

                # Generate guide with tracing enabled
                result = agent.generate_interview_guide(input_data, enable_tracing=True)

                # Display results
                st.success("✅ Interview guide generated successfully!")

                # Show metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Handle both string and enum types
                    interview_type_display = (
                        result.interview_type.value
                        if hasattr(result.interview_type, "value")
                        else str(result.interview_type)
                    )
                    st.metric("Interview Type", interview_type_display)
                with col2:
                    st.metric("Prep Time", result.estimated_prep_time or "2-3 hours")
                with col3:
                    if result.job_title_extracted:
                        st.metric("Position", result.job_title_extracted)

                # Display the guide
                st.markdown("---")
                st.markdown("## 📖 Your Interview Preparation Guide")
                st.markdown(result.guide_content)

                # Download option
                st.markdown("---")
                st.subheader("💾 Download Your Guide")

                # Create filename
                safe_job_title = (
                    (result.job_title_extracted or "Interview")
                    .replace(" ", "_")
                    .replace("/", "_")
                )
                # Handle both string and enum types for filename
                interview_type_str = (
                    result.interview_type.value
                    if hasattr(result.interview_type, "value")
                    else str(result.interview_type)
                )
                filename = f"Interview_Guide_{safe_job_title}_{interview_type_str.replace(' ', '_')}.txt"

                st.download_button(
                    label="📄 Download as Text File",
                    data=result.guide_content,
                    file_name=filename,
                    mime="text/plain",
                    help="Download your interview guide for offline reference",
                )

                # Success message
                st.info(
                    """
                **💡 Next Steps:**
                1. Review the guide thoroughly
                2. Practice your answers out loud
                3. Research the company further if needed
                4. Prepare specific examples from your experience
                5. Get a good night's sleep before the interview!
                """
                )

            except Exception as e:
                st.error(f"❌ Failed to generate interview guide: {str(e)}")
                st.info(
                    "Please check your inputs and try again. If the problem persists, verify your API key is correct."
                )


# For testing/direct running
if __name__ == "__main__":
    show_interview_preparation_page()
