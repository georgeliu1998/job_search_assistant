"""Interview Preparation page for the Streamlit app."""

from datetime import datetime
from typing import Optional

import streamlit as st

from src.agent.tools.pii_redaction import pii_pipeline
from src.agent.workflows.interview_prep.main import (
    get_interview_prep_workflow,
    run_interview_prep_workflow,
)
from src.agent.workflows.interview_prep.states import InterviewPrepState
from src.models.interview import (
    DEFAULT_DURATIONS,
    QUESTION_MIXES,
    DifficultyLevel,
    InterviewDetails,
    InterviewFormat,
    InterviewType,
    QuestionCategory,
)


def render_interview_prep_page():
    """Render the Interview Preparation page."""
    st.header("🧭 Interview Preparation")
    st.markdown("""
        Prepare for your upcoming interview with personalized questions, answers,
        and research insights tailored to your background and the specific role.
        """)

    # Initialize session state
    if "interview_guide" not in st.session_state:
        st.session_state.interview_guide = None
    if "prep_state" not in st.session_state:
        st.session_state.prep_state = None
    if "pii_approved" not in st.session_state:
        st.session_state.pii_approved = False
    if "pending_workflow_state" not in st.session_state:
        st.session_state.pending_workflow_state = None

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

    # Panel interview detection is now handled automatically via format selection

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

    # Interviewer count is no longer needed for question generation

    # Question preview
    st.subheader("📊 Question Configuration")

    # Show question breakdown based on selected interview type
    try:
        interview_type_enum = InterviewType(interview_type)
        question_mix = QUESTION_MIXES.get(interview_type_enum, {})
        duration = DEFAULT_DURATIONS.get(interview_type_enum, 60)

        if question_mix:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Expected Duration:** {duration} minutes")
                st.write("**Question Breakdown:**")
                total_questions = 0
                for category, count in question_mix.items():
                    if count > 0:
                        st.write(f"• {category.replace('_', ' ').title()}: {count}")
                        total_questions += count
                st.write(f"**Total Questions:** {total_questions}")

            with col2:
                st.write("**Interview Focus:**")
                if interview_type_enum == InterviewType.HR_SCREEN:
                    st.write("• Cultural fit assessment")
                    st.write("• Basic qualifications")
                    st.write("• Behavioral evaluation")
                elif interview_type_enum == InterviewType.HIRING_MANAGER:
                    st.write("• Leadership assessment")
                    st.write("• Technical judgment")
                    st.write("• System thinking")
                elif interview_type_enum == InterviewType.PEER:
                    st.write("• Technical deep-dive")
                    st.write("• Problem-solving skills")
                    st.write("• Team collaboration")
        else:
            st.warning("Question breakdown not available for selected interview type.")
    except Exception as e:
        st.warning(f"Could not load question configuration: {e}")

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
        from src.agent.tools.pii_redaction import pii_pipeline

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
            # Reset previous state
            st.session_state.pii_approved = False
            st.session_state.pending_workflow_state = None
            st.session_state.prep_state = None

            generate_interview_guide(
                job_description=job_description,
                resume_text=resume_text,
                interview_type=interview_type,
                interview_format=interview_format,
                company=company,
                role=role,
            )

    # Check if PII is approved and we have a pending workflow to run
    if st.session_state.pii_approved and st.session_state.pending_workflow_state:
        # Add visual separator
        st.markdown("---")
        st.subheader("🚀 Generating Your Interview Guide")

        # Run the workflow outside the expander context
        process_interview_workflow(st.session_state.pending_workflow_state)
        # Clear the pending state
        st.session_state.pii_approved = False
        st.session_state.pending_workflow_state = None

    # Display results
    if st.session_state.prep_state:
        display_interview_guide()


def generate_interview_guide(
    job_description: str,
    resume_text: str,
    interview_type: str,
    interview_format: str,
    company: Optional[str],
    role: Optional[str],
):
    """Generate the interview preparation guide."""
    try:
        # Create interview details
        interview_details = InterviewDetails(
            type=InterviewType(interview_type),
            format=InterviewFormat(interview_format),
            company=company or None,
            role=role or None,
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
                    st.session_state.pii_approved = True
                    st.session_state.pending_workflow_state = initial_state
                    st.rerun()
            else:
                st.success("✅ Resume successfully redacted")
                st.text_area(
                    "Redacted Resume",
                    redaction_result.redacted_resume_text,
                    height=150,
                    key="redaction_success",
                )
                # Auto-approve if redaction is complete
                st.session_state.pii_approved = True
                st.session_state.pending_workflow_state = initial_state

    except Exception as e:
        st.error(f"Error generating interview guide: {str(e)}")


def process_interview_workflow(initial_state: InterviewPrepState):
    """Process the interview preparation workflow."""
    import threading
    import time
    from concurrent.futures import Future, ThreadPoolExecutor

    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Progress steps with corresponding messages
    progress_steps = [
        (10, "🔒 Validating and redacting personal information..."),
        (25, "🔍 Researching company and role..."),
        (50, "❓ Generating interview questions..."),
        (75, "💡 Creating personalized answers..."),
        (90, "📋 Compiling your interview guide..."),
        (100, "✅ Finalizing your interview guide..."),
    ]

    try:
        # Start the workflow in a separate thread
        workflow_future: Future = None
        result = None
        error = None

        def run_workflow():
            nonlocal result, error
            try:
                result = run_interview_prep_workflow(initial_state)
            except Exception as e:
                error = e

        # Start workflow execution
        with ThreadPoolExecutor(max_workers=1) as executor:
            workflow_future = executor.submit(run_workflow)

            # Update progress while workflow is running
            current_step = 0
            while current_step < len(progress_steps) and not workflow_future.done():
                progress_value, progress_message = progress_steps[current_step]
                status_text.text(progress_message)
                progress_bar.progress(progress_value)

                # Wait a bit before next update, but check if workflow is done
                for _ in range(
                    10
                ):  # Check every 0.5 seconds for 5 seconds total per step
                    if workflow_future.done():
                        break
                    time.sleep(0.5)

                current_step += 1

            # Wait for workflow to complete
            workflow_future.result()  # This will raise any exception that occurred

        # Check for errors
        if error:
            raise error

        if result and result.get("error"):
            st.error(f"Workflow error: {result['error']}")
            return

        # Final progress update
        status_text.text("✅ Interview guide generated successfully!")
        progress_bar.progress(100)

        # Store results
        st.session_state.prep_state = result

        # Brief pause to show completion
        time.sleep(0.5)

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
            f"❓ Interview Questions & Answers ({len(guide.qa_pairs)} questions generated)"
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
                accessibility_indicator = "✅" if citation.is_accessible else "❌"
                st.markdown(f"{accessibility_indicator} **{citation.title}**")
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
        accessible_sources = sum(1 for c in guide.citations if c.is_accessible)
        st.metric(
            "Accessible Sources",
            (
                f"{accessible_sources}/{len(guide.citations)}"
                if guide.citations
                else "0/0"
            ),
        )

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
