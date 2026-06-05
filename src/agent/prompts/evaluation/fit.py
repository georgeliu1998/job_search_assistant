"""
Fit assessment prompt for structured outputs.

Guides the LLM to judge whether a job's focus (responsibilities, required
skills, domain) matches the user's target role and skills -- strictly a
subject-matter alignment judgment, not a hiring-likelihood one -- based on the
role's actual focus areas rather than the title alone.
"""

from langchain_core.prompts import PromptTemplate

FIT_ASSESSMENT_RAW_TEMPLATE = """
You are judging whether a job's focus matches a candidate's target role and
skills. Judge only the alignment of subject matter -- do NOT speculate about
whether the candidate would get hired or be a strong applicant (you do not have
their full background; that decision is made elsewhere).

Compare the candidate's target role and key skills against the job's actual
focus areas, responsibilities, and required skills. Do not rely on the job
title alone -- a similar title with a different focus may still be a poor match
(for example, a "Data Scientist" who builds LLM-driven applications is a poor
match for a "Data Scientist" role focused on A/B testing and analytics).

Return:
- verdict: "good_fit" if the role's focus matches the candidate's target role
  and skills; otherwise "poor_fit".
- reasoning: one or two sentences explaining the verdict, referring only to
  subject-matter alignment.

Candidate's target role:
{target_role_description}

Candidate's key skills:
{key_skills}

Job posting:
{job_text}
"""

FIT_ASSESSMENT_PROMPT = PromptTemplate.from_template(FIT_ASSESSMENT_RAW_TEMPLATE)
