"""
Job posting extraction prompt for structured outputs.

This prompt is optimized for use with LangChain's structured outputs feature,
focusing on clear instructions without JSON formatting requirements.
"""

from langchain_core.prompts import PromptTemplate

JOB_POSTING_EXTRACTION_RAW_TEMPLATE = """
Extract structured information from this job posting.

Follow these rules:
- Salary: report annual amounts in USD. If the posting lists multiple salary
  ranges (for example, different ranges per location or level), extract the
  HIGHEST range. `salary_min` and `salary_max` must reflect that top-paying
  range.
- seniority_level: infer from the title and responsibilities (junior, mid,
  senior, staff, principal, lead). Use "unclear" if it cannot be determined.
- visa_sponsorship: "yes" if the posting states sponsorship is available, "no"
  if it states sponsorship is not available, otherwise "unclear".
- employment_type: full-time, part-time, contract, or internship; "unclear" if
  not stated.
- travel_required: "yes" if the role requires travel, "no" if it states no
  travel, otherwise "unclear".
- education_requirement: the MINIMUM degree required (associate, bachelor,
  master, phd). Use "none" only if the posting explicitly says no degree is
  required, and "unclear" if education is not mentioned.
- equity_offered: list any equity types mentioned (stock_options, rsus). Leave
  empty if equity is not mentioned.
- benefits_offered: list any benefits mentioned (health, vision, dental, life,
  std, ltd, 401k, pto). Leave empty if benefits are not mentioned.
- For any field not mentioned in the posting, use its default ("unclear" or an
  empty list) rather than guessing.

Job posting:

{job_text}
"""

JOB_POSTING_EXTRACTION_PROMPT = PromptTemplate.from_template(JOB_POSTING_EXTRACTION_RAW_TEMPLATE)
