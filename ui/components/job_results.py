"""
Job evaluation results display component
"""

from typing import Any, Dict

import streamlit as st


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
