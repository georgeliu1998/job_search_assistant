"""
Job evaluation results display component.
"""

from typing import Any, Dict

import streamlit as st

# Human-readable labels for the criteria keys produced by the evaluator.
CRITERION_LABELS = {
    "salary": "Salary",
    "location": "Location",
    "level": "Role Type",
    "seniority": "Seniority",
    "visa": "Visa Sponsorship",
    "blacklist": "Company Blacklist",
    "employment_type": "Employment Type",
    "travel": "Travel",
    "education": "Education",
    "equity": "Equity",
    "benefits": "Benefits",
    "fit": "Fit",
}


def _criterion_icon(result: Dict[str, Any]) -> str:
    """Pick an icon based on pass/fail and required/optional mode."""
    passed = result.get("pass")
    required = result.get("mode") == "required"
    if passed:
        return "✅" if required else "🟢"
    return "❌" if required else "🟡"


def _display_extracted_info(extracted_info: Dict[str, Any]) -> None:
    """Render the structured fields extracted from the posting."""
    st.subheader("📋 Extracted Job Information")
    col1, col2 = st.columns(2)

    with col1:
        if extracted_info.get("title"):
            st.write(f"**Title:** {extracted_info['title']}")
        if extracted_info.get("company"):
            st.write(f"**Company:** {extracted_info['company']}")
        location = extracted_info.get("location_policy")
        if location and location != "unclear":
            st.write(f"**Location:** {location.title()}")
        role_type = extracted_info.get("role_type")
        if role_type and role_type != "unclear":
            role_display = "Individual Contributor" if role_type == "ic" else "Manager"
            st.write(f"**Role Type:** {role_display}")
        seniority = extracted_info.get("seniority_level")
        if seniority and seniority != "unclear":
            st.write(f"**Seniority:** {seniority.title()}")
        employment = extracted_info.get("employment_type")
        if employment and employment != "unclear":
            st.write(f"**Employment Type:** {employment.title()}")

    with col2:
        salary_min = extracted_info.get("salary_min")
        salary_max = extracted_info.get("salary_max")
        if salary_min and salary_max:
            st.write(f"**Salary:** ${salary_min:,} - ${salary_max:,}")
        elif salary_max:
            st.write(f"**Salary:** Up to ${salary_max:,}")
        elif salary_min:
            st.write(f"**Salary:** From ${salary_min:,}")

        visa = extracted_info.get("visa_sponsorship")
        if visa and visa != "unclear":
            st.write(f"**Visa Sponsorship:** {visa.title()}")
        travel = extracted_info.get("travel_required")
        if travel and travel != "unclear":
            st.write(f"**Travel Required:** {travel.title()}")
        education = extracted_info.get("education_requirement")
        if education and education != "unclear":
            st.write(f"**Education Required:** {education.title()}")
        equity = extracted_info.get("equity_offered")
        if equity:
            st.write(f"**Equity:** {', '.join(equity)}")
        benefits = extracted_info.get("benefits_offered")
        if benefits:
            st.write(f"**Benefits:** {', '.join(benefits)}")


def _display_criteria(evaluation_result: Dict[str, Any]) -> None:
    """Render each criterion result with a pass/fail and required/optional badge."""
    st.subheader("🧮 Criteria Breakdown")
    st.caption("✅ required pass  ❌ required fail  🟢 optional pass  🟡 optional fail")
    for key, result in evaluation_result.items():
        if not isinstance(result, dict) or "pass" not in result:
            continue
        label = CRITERION_LABELS.get(key, key.replace("_", " ").title())
        icon = _criterion_icon(result)
        st.write(f"{icon} **{label}:** {result.get('reason', '')}")


def display_job_evaluation_results(results: Dict[str, Any]) -> None:
    """Display job evaluation results in a formatted way."""
    recommendation = results.get("recommendation", "Unknown")
    reasoning = results.get("reasoning", "No reasoning provided")
    extracted_info = results.get("extracted_info", {})
    evaluation_result = results.get("evaluation_result", {})

    if recommendation == "APPLY":
        st.success(f"🎯 **Recommendation: {recommendation}**")
        st.success(f"**Reasoning:** {reasoning}")
    else:
        st.error(f"❌ **Recommendation: {recommendation}**")
        st.error(f"**Reasoning:** {reasoning}")

    if evaluation_result:
        _display_criteria(evaluation_result)

    if extracted_info:
        _display_extracted_info(extracted_info)
