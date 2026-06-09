"""
Settings page: job evaluation preferences.

Lets the user configure the preferences used by the job evaluation workflow and
persists them to a local YAML file.
"""

import streamlit as st

from src.core.preferences import load_preferences, save_preferences
from src.models.user import CriterionConfig, JobPreferences

SALARY_TIERS = [60000, 80000, 100000, 120000, 140000, 160000, 180000, 200000]

LOCATION_LABELS = {"onsite": "On-site", "remote": "Remote", "hybrid": "Hybrid"}
LEVEL_LABELS = {"ic": "Individual Contributor", "manager": "Manager"}
SENIORITY_LABELS = {
    "junior": "Junior",
    "mid": "Mid",
    "senior": "Senior",
    "staff": "Staff",
    "principal": "Principal",
    "lead": "Lead",
}
EMPLOYMENT_LABELS = {
    "full-time": "Full-time",
    "part-time": "Part-time",
    "contract": "Contract",
    "internship": "Internship",
}
EQUITY_LABELS = {"stock_options": "Stock Options", "rsus": "RSUs"}
BENEFIT_LABELS = {
    "health": "Health/Medical",
    "vision": "Vision",
    "dental": "Dental",
    "life": "Life",
    "std": "STD",
    "ltd": "LTD",
    "401k": "401K",
    "pto": "PTO",
}
EDUCATION_LABELS = {
    "associate": "Associate Degree",
    "bachelor": "Bachelor's Degree",
    "master": "Master's Degree",
    "phd": "PhD",
}

# (config attribute, display label) for the per-criterion advanced settings.
CRITERIA_CONFIGS = [
    ("salary_config", "Salary"),
    ("location_config", "Location"),
    ("level_config", "Role Type"),
    ("seniority_config", "Seniority"),
    ("visa_config", "Visa Sponsorship"),
    ("blacklist_config", "Company Blacklist"),
    ("employment_type_config", "Employment Type"),
    ("travel_config", "Travel"),
    ("education_config", "Education"),
    ("equity_config", "Equity"),
    ("benefits_config", "Benefits"),
    ("fit_config", "Fit"),
]


def _multiselect(label, options_map, current, help_text=None, key=None):
    """Render a multiselect using display labels; return selected internal values."""
    labels = list(options_map.values())
    label_to_value = {v: k for k, v in options_map.items()}
    default_labels = [options_map[v] for v in current if v in options_map]
    selected = st.multiselect(label, labels, default=default_labels, help=help_text, key=key)
    return [label_to_value[s] for s in selected]


# session_state keys for the value widgets. The advanced-config widget keys are
# derived from CRITERIA_CONFIGS. All are cleared on "Reset to Defaults" so the
# widgets re-initialize from the freshly written defaults instead of showing the
# user's prior selections (Streamlit persists keyed widget state across reruns).
_VALUE_WIDGET_KEYS = [
    "pref_min_salary",
    "pref_equity",
    "pref_benefits",
    "pref_locations",
    "pref_travel",
    "pref_employment",
    "pref_levels",
    "pref_seniority",
    "pref_education",
    "pref_visa",
    "pref_blacklist",
    "pref_target_role",
    "pref_key_skills",
]


def _all_widget_keys() -> list:
    """All session_state keys used by the settings widgets (value + advanced)."""
    keys = list(_VALUE_WIDGET_KEYS)
    for attr, _ in CRITERIA_CONFIGS:
        keys.extend((f"{attr}_mode", f"{attr}_none"))
    return keys


def _salary_slider_options(persisted: int) -> list:
    """Return the salary tier options, always including the persisted value.

    Folding the persisted value in (rather than indexing into a fixed list)
    means a hand-edited or out-of-tier salary is shown as-is instead of being
    silently clamped to a default tier on the next save.
    """
    return sorted(set(SALARY_TIERS) | {persisted})


def _validate_required_lists(
    acceptable_locations: list,
    acceptable_employment_types: list,
    acceptable_levels: list,
    acceptable_seniority: list,
) -> list[str]:
    """Return human-readable error messages for empty membership lists.

    These four criteria are list-membership checks. An empty list combined
    with any stated value in the posting always produces a fail, which is
    never what the user wants -- so we require at least one selection.
    """
    errors = []
    if not acceptable_locations:
        errors.append("at least one acceptable location")
    if not acceptable_employment_types:
        errors.append("at least one acceptable employment type")
    if not acceptable_levels:
        errors.append("at least one acceptable role type")
    if not acceptable_seniority:
        errors.append("at least one acceptable seniority level")
    return errors


def render_settings_page():
    """Render the job preferences settings page."""
    st.header("⚙️ Job Preferences")
    st.markdown(
        "Configure how job postings are evaluated. Preferences are saved "
        "locally and used the next time you evaluate a job."
    )

    prefs = load_preferences()

    st.subheader("💰 Compensation")
    min_salary = st.select_slider(
        "Minimum yearly salary",
        options=_salary_slider_options(prefs.min_salary),
        value=prefs.min_salary,
        format_func=lambda v: f"${v:,}",
        key="pref_min_salary",
    )
    acceptable_equity_types = _multiselect(
        "Acceptable equity types",
        EQUITY_LABELS,
        prefs.acceptable_equity_types,
        "Leave empty if you have no equity preference.",
        key="pref_equity",
    )
    required_benefits = _multiselect(
        "Required benefits",
        BENEFIT_LABELS,
        prefs.required_benefits,
        "Leave empty if you have no benefits requirement.",
        key="pref_benefits",
    )

    st.subheader("🏢 Work Arrangement")
    acceptable_locations = _multiselect(
        "Acceptable locations",
        LOCATION_LABELS,
        prefs.acceptable_locations,
        key="pref_locations",
    )
    willing_to_travel = st.toggle(
        "I'm willing to travel", value=prefs.willing_to_travel, key="pref_travel"
    )
    acceptable_employment_types = _multiselect(
        "Acceptable employment types",
        EMPLOYMENT_LABELS,
        prefs.acceptable_employment_types,
        key="pref_employment",
    )

    st.subheader("📋 Requirements")
    acceptable_levels = _multiselect(
        "Acceptable role types",
        LEVEL_LABELS,
        prefs.acceptable_levels,
        key="pref_levels",
    )
    acceptable_seniority = _multiselect(
        "Acceptable seniority levels",
        SENIORITY_LABELS,
        prefs.acceptable_seniority,
        key="pref_seniority",
    )
    education_values = list(EDUCATION_LABELS.keys())
    education_level = st.selectbox(
        "Your highest education level",
        education_values,
        index=education_values.index(prefs.education_level),
        format_func=lambda v: EDUCATION_LABELS[v],
        key="pref_education",
    )
    visa_sponsorship_required = st.toggle(
        "I require visa sponsorship",
        value=prefs.visa_sponsorship_required,
        key="pref_visa",
    )
    blacklist_text = st.text_area(
        "Company blacklist (one per line)",
        value="\n".join(prefs.company_blacklist),
        help="Postings from these companies will fail the blacklist check.",
        key="pref_blacklist",
    )
    company_blacklist = [line.strip() for line in blacklist_text.splitlines() if line.strip()]

    st.subheader("🎯 Fit")
    target_role_description = st.text_area(
        "Target role description",
        value=prefs.target_role_description,
        placeholder=("e.g. AI/ML Engineer focused on LLMs, RAG, and production ML systems"),
        help="Used by the AI fit assessment. Leave empty to skip fit evaluation.",
        key="pref_target_role",
    )
    key_skills_text = st.text_input(
        "Key skills (comma-separated)",
        value=", ".join(prefs.key_skills),
        placeholder="Python, PyTorch, LangChain, RAG",
        key="pref_key_skills",
    )
    key_skills = [s.strip() for s in key_skills_text.split(",") if s.strip()]

    # Collect per-criterion mode / none-handling configuration.
    criteria_configs = {}
    with st.expander("🔧 Advanced Configuration", expanded=False):
        st.caption(
            "Mark each criterion as required (must pass to recommend APPLY) or "
            "optional, and choose how to treat a posting that doesn't mention it."
        )
        for attr, label in CRITERIA_CONFIGS:
            current = getattr(prefs, attr)
            col1, col2 = st.columns(2)
            with col1:
                mode = st.selectbox(
                    f"{label} — mode",
                    ["required", "optional"],
                    index=["required", "optional"].index(current.mode.value),
                    format_func=str.capitalize,
                    key=f"{attr}_mode",
                )
            with col2:
                none_policy = st.selectbox(
                    f"{label} — if not in posting",
                    ["pass", "fail"],
                    index=["pass", "fail"].index(current.none_policy.value),
                    format_func=lambda v: "Count as pass" if v == "pass" else "Count as fail",
                    key=f"{attr}_none",
                )
            criteria_configs[attr] = CriterionConfig(mode=mode, none_policy=none_policy)

    validation_errors = _validate_required_lists(
        acceptable_locations,
        acceptable_employment_types,
        acceptable_levels,
        acceptable_seniority,
    )
    if validation_errors:
        st.error("Please select " + "; ".join(validation_errors) + " before saving.")

    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button(
            "💾 Save Preferences",
            type="primary",
            use_container_width=True,
            disabled=bool(validation_errors),
        ):
            new_prefs = JobPreferences(
                min_salary=min_salary,
                acceptable_locations=acceptable_locations,
                acceptable_levels=acceptable_levels,
                acceptable_seniority=acceptable_seniority,
                visa_sponsorship_required=visa_sponsorship_required,
                company_blacklist=company_blacklist,
                acceptable_employment_types=acceptable_employment_types,
                willing_to_travel=willing_to_travel,
                education_level=education_level,
                acceptable_equity_types=acceptable_equity_types,
                required_benefits=required_benefits,
                target_role_description=target_role_description,
                key_skills=key_skills,
                **criteria_configs,
            )
            save_preferences(new_prefs)
            st.success("Preferences saved.")

    with col_reset:
        if st.button("↺ Reset to Defaults", use_container_width=True):
            save_preferences(JobPreferences())
            # Clear persisted widget state so the inputs re-initialize from the
            # freshly written defaults instead of the user's prior selections.
            for key in _all_widget_keys():
                st.session_state.pop(key, None)
            st.rerun()
