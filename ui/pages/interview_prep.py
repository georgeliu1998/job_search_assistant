"""Interview Preparation page for the Streamlit app."""

from datetime import datetime
from typing import Optional

import streamlit as st

from src.agent.tools.interview.pii_redaction import pii_pipeline
from src.agent.workflows.interview_prep.main import get_interview_prep_workflow
from src.agent.workflows.interview_prep.states import InterviewPrepState
from src.models.interview import (
    DifficultyLevel,
    InterviewDetails,
    InterviewFormat,
    InterviewType,
    QuestionCategory,
)


def render_interview_prep_page():
    """Render the Interview Preparation page."""
    st.header("🧭 Interview Preparation")
    st.markdown(
        """
        Prepare for your upcoming interview with personalized questions, answers,
        and research insights tailored to your background and the specific role.
        """
    )

    # Initialize session state
    if "interview_guide" not in st.session_state:
        st.session_state.interview_guide = None
    if "prep_state" not in st.session_state:
        st.session_state.prep_state = None

    # Input section
    st.subheader("📝 Interview Details")

    col1, col2 = st.columns(2)

    with col1:
        interview_type = st.selectbox(
            "Interview Type",
            [t.value for t in InterviewType],
            help="What type of interview is this?",
        )

        interview_format = st.selectbox(
            "Interview Format",
            [f.value for f in InterviewFormat],
            help="What format will the interview be conducted in?",
        )

        is_panel = st.checkbox(
            "Panel Interview", help="Multiple interviewers will be present"
        )

    with col2:
        company = st.text_input(
            "Company Name",
            placeholder="e.g., Google, Microsoft, etc.",
            help="Company you're interviewing with",
        )

        role = st.text_input(
            "Role Title",
            placeholder="e.g., Senior Software Engineer, Product Manager",
            help="The specific role you're applying for",
        )

        if is_panel:
            interviewer_count = st.number_input(
                "Number of Interviewers",
                min_value=2,
                max_value=10,
                value=3,
                help="How many people will be interviewing you?",
            )
        else:
            interviewer_count = 1

    st.subheader("📄 Required Information")

    job_description = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the job description here...",
        help="Copy and paste the complete job posting",
    )

    resume_text = st.text_area(
        "Your Resume Content",
        height=300,
        placeholder="Paste your resume content here...",
        help="Your resume will be processed to remove personal information for privacy",
    )

    # Privacy notice with PII detection method info
    try:
        from src.agent.tools.interview.pii_redaction import pii_pipeline

        if pii_pipeline.presidio_available is None:
            pii_method = (
                "Will be determined automatically (Presidio preferred, regex fallback)"
            )
        elif pii_pipeline.presidio_available:
            pii_method = "Microsoft Presidio (enterprise-grade NLP-based detection)"
        else:
            pii_method = "Regex patterns (basic pattern matching)"
        st.info(
            f"🔒 **Privacy Notice**: Your resume will be automatically redacted to remove personal information (names, emails, phone numbers) before being processed by AI models.\n\n**PII Detection Method**: {pii_method}"
        )
    except:
        st.info(
            "🔒 **Privacy Notice**: Your resume will be automatically redacted to remove personal information (names, emails, phone numbers) before being processed by AI models."
        )

    # Generate button
    if st.button("🚀 Generate Interview Guide", type="primary"):
        if not job_description or not resume_text:
            st.error("Please provide both job description and resume content.")
        else:
            generate_interview_guide(
                job_description=job_description,
                resume_text=resume_text,
                interview_type=interview_type,
                interview_format=interview_format,
                is_panel=is_panel,
                company=company,
                role=role,
                interviewer_count=interviewer_count,
            )

    # Display results
    if st.session_state.prep_state:
        display_interview_guide()


def generate_interview_guide(
    job_description: str,
    resume_text: str,
    interview_type: str,
    interview_format: str,
    is_panel: bool,
    company: Optional[str],
    role: Optional[str],
    interviewer_count: int,
):
    """Generate the interview preparation guide."""
    with st.spinner("🔍 Processing your information..."):
        try:
            # Create interview details
            interview_details = InterviewDetails(
                type=InterviewType(interview_type),
                format=InterviewFormat(interview_format),
                is_panel=is_panel,
                company=company or None,
                role=role or None,
                interviewer_count=interviewer_count,
            )

            # Create initial state
            initial_state = InterviewPrepState(
                job_description=job_description,
                resume_text=resume_text,
                interview_details=interview_details,
            )

            # Show PII redaction preview first
            st.subheader("🔒 Privacy Review")
            with st.expander("Review Redacted Resume", expanded=False):
                redaction_result = pii_pipeline.redact_resume(resume_text)

                if not redaction_result.complete:
                    st.warning("⚠️ PII redaction needs manual review")
                    st.text_area(
                        "Redacted Resume (Please Review)",
                        redaction_result.redacted_resume_text,
                        height=200,
                        key="redaction_preview",
                    )

                    if st.button("✅ Approve and Continue"):
                        process_interview_workflow(initial_state)
                else:
                    st.success("✅ Resume successfully redacted")
                    st.text_area(
                        "Redacted Resume",
                        redaction_result.redacted_resume_text,
                        height=150,
                        key="redaction_success",
                    )
                    process_interview_workflow(initial_state)

        except Exception as e:
            st.error(f"Error generating interview guide: {str(e)}")


def process_interview_workflow(initial_state: InterviewPrepState):
    """Process the interview preparation workflow."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Get workflow
        workflow = get_interview_prep_workflow()

        # Execute workflow with progress updates
        status_text.text("🔒 Validating and redacting personal information...")
        progress_bar.progress(20)

        result = workflow.invoke(initial_state)

        # Handle workflow errors - result is a LangGraph state dict
        if result.get("error"):
            st.error(f"Workflow error: {result['error']}")
            return

        status_text.text("🔍 Researching company and role...")
        progress_bar.progress(40)

        status_text.text("❓ Generating interview questions...")
        progress_bar.progress(60)

        status_text.text("💡 Creating personalized answers...")
        progress_bar.progress(80)

        status_text.text("📋 Compiling your interview guide...")
        progress_bar.progress(100)

        # Store results
        st.session_state.prep_state = result

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        st.success("✅ Interview guide generated successfully!")

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error processing workflow: {str(e)}")


def display_interview_guide():
    """Display the generated interview guide."""
    state = st.session_state.prep_state

    if not state or not state.get("interview_guide"):
        return

    guide = state.get("interview_guide")

    # Guide header
    st.subheader("📋 Your Interview Preparation Guide")

    # Interview summary
    if guide.research_summary:
        with st.expander("🔍 Research Summary", expanded=True):
            st.markdown(guide.research_summary)

    # Questions and answers
    if guide.qa_pairs:
        st.subheader(
            f"❓ Interview Questions & Answers ({len(guide.qa_pairs)} questions)"
        )

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All"] + [cat.value for cat in QuestionCategory],
                key="category_filter",
            )
        with col2:
            difficulty_filter = st.selectbox(
                "Filter by Difficulty",
                ["All"] + [diff.value for diff in DifficultyLevel],
                key="difficulty_filter",
            )

        # Filter questions
        filtered_pairs = guide.qa_pairs
        if category_filter != "All":
            filtered_pairs = [
                qa for qa in filtered_pairs if qa.question.category == category_filter
            ]
        if difficulty_filter != "All":
            filtered_pairs = [
                qa
                for qa in filtered_pairs
                if qa.question.difficulty == difficulty_filter
            ]

        # Display questions
        for i, qa_pair in enumerate(filtered_pairs, 1):
            with st.expander(f"Q{i}: {qa_pair.question.question}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.badge(qa_pair.question.category.title())
                with col2:
                    difficulty_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
                    st.write(
                        f"{difficulty_colors.get(qa_pair.question.difficulty, '⚪')} {qa_pair.question.difficulty.title()}"
                    )
                with col3:
                    st.write(f"Style: {qa_pair.answer.style.title()}")

                st.markdown("**Why this question matters:**")
                st.write(qa_pair.question.rationale)

                st.markdown("**Suggested Answer:**")
                st.write(qa_pair.answer.answer)

                if qa_pair.answer.key_points:
                    st.markdown("**Key Points to Remember:**")
                    for point in qa_pair.answer.key_points:
                        st.write(f"• {point}")

                if qa_pair.answer.examples:
                    st.markdown("**Examples from Your Background:**")
                    for example in qa_pair.answer.examples:
                        st.write(f"• {example}")

    # Preparation tips
    if guide.preparation_tips:
        with st.expander("💡 Preparation Tips", expanded=True):
            for tip in guide.preparation_tips:
                st.write(f"• {tip}")

    # Citations
    if guide.citations:
        with st.expander(
            f"📚 Research Sources ({len(guide.citations)} sources)", expanded=False
        ):
            for citation in guide.citations:
                reliability_emoji = (
                    "🔴"
                    if citation.reliability_score < 0.5
                    else "🟡" if citation.reliability_score < 0.8 else "🟢"
                )
                st.markdown(f"{reliability_emoji} **{citation.title}**")
                st.markdown(f"🔗 [{citation.url}]({citation.url})")
                st.markdown(
                    f"📅 Accessed: {citation.accessed_at.strftime('%Y-%m-%d %H:%M')}"
                )
                if citation.content_snippet:
                    st.markdown(f"📄 *{citation.content_snippet}*")
                st.markdown("---")

    # Download/export options
    st.subheader("📥 Export Options")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Download as Text"):
            guide_text = format_guide_as_text(guide)
            st.download_button(
                label="📄 Download Guide.txt",
                data=guide_text,
                file_name=f"interview_guide_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )

    with col2:
        if st.button("📊 View Summary Stats"):
            display_guide_stats(guide)


def format_guide_as_text(guide) -> str:
    """Format the interview guide as plain text."""
    text_parts = []

    text_parts.append("INTERVIEW PREPARATION GUIDE")
    text_parts.append("=" * 40)
    text_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    text_parts.append("")

    if guide.research_summary:
        text_parts.append("RESEARCH SUMMARY")
        text_parts.append("-" * 20)
        text_parts.append(guide.research_summary)
        text_parts.append("")

    if guide.qa_pairs:
        text_parts.append("QUESTIONS & ANSWERS")
        text_parts.append("-" * 20)

        for i, qa_pair in enumerate(guide.qa_pairs, 1):
            text_parts.append(f"Q{i}: {qa_pair.question.question}")
            text_parts.append(f"Category: {qa_pair.question.category}")
            text_parts.append(f"Difficulty: {qa_pair.question.difficulty}")
            text_parts.append(f"Rationale: {qa_pair.question.rationale}")
            text_parts.append("")
            text_parts.append("Answer:")
            text_parts.append(qa_pair.answer.answer)
            text_parts.append("")

            if qa_pair.answer.key_points:
                text_parts.append("Key Points:")
                for point in qa_pair.answer.key_points:
                    text_parts.append(f"• {point}")
                text_parts.append("")

            text_parts.append("-" * 40)
            text_parts.append("")

    if guide.preparation_tips:
        text_parts.append("PREPARATION TIPS")
        text_parts.append("-" * 20)
        for tip in guide.preparation_tips:
            text_parts.append(f"• {tip}")
        text_parts.append("")

    if guide.citations:
        text_parts.append("SOURCES")
        text_parts.append("-" * 20)
        for citation in guide.citations:
            text_parts.append(f"• {citation.title}")
            text_parts.append(f"  {citation.url}")
            text_parts.append(
                f"  Accessed: {citation.accessed_at.strftime('%Y-%m-%d %H:%M')}"
            )
            text_parts.append("")

    return "\n".join(text_parts)


def display_guide_stats(guide):
    """Display statistics about the interview guide."""
    st.subheader("📊 Guide Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Questions", len(guide.qa_pairs))

    with col2:
        st.metric("Research Sources", len(guide.citations))

    with col3:
        st.metric("Preparation Tips", len(guide.preparation_tips))

    with col4:
        avg_reliability = (
            sum(c.reliability_score for c in guide.citations) / len(guide.citations)
            if guide.citations
            else 0
        )
        st.metric("Avg Source Reliability", f"{avg_reliability:.1f}")

    if guide.qa_pairs:
        # Question category breakdown
        category_counts = {}
        difficulty_counts = {}

        for qa_pair in guide.qa_pairs:
            category = qa_pair.question.category
            difficulty = qa_pair.question.difficulty

            category_counts[category] = category_counts.get(category, 0) + 1
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Questions by Category:**")
            for category, count in category_counts.items():
                st.write(f"• {category.title()}: {count}")

        with col2:
            st.write("**Questions by Difficulty:**")
            for difficulty, count in difficulty_counts.items():
                st.write(f"• {difficulty.title()}: {count}")
